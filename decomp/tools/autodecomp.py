#!/usr/bin/env python3
"""Turn Ghidra's decompilation (ghidra/AutoExport.java) into C files that build.py can compile and link.

Every function whose decompiled text has no constructs that cannot be compiled faithfully (indirect calls with
unknown conventions, registers the decompiler could not attribute, SEH frames, bad instructions, ...) becomes
    DECOMP(XXXXXXXX) RET CC f_XXXXXXXX(PARAMS) { ... }
with its callees declared as sub_XXXXXXXX and its globals as G_XXXXXXXX over the original data (d_XXXXXXXX).
Each function is compiled on its own first; the ones that compile are grouped into translation units.
The result is raw decompiler output - correct only as far as Ghidra is - so tools/difftest.py --auto checks
every function against the original in the emulator before it is trusted.

usage: autodecomp.py AUTO.jsonl TYPES.h OUTDIR --exe EXE --functions symbols/GAME_functions.tsv [--syms S] [--max N]
Output (OUTDIR, keep it out of the public repository: it is the game's code): auto_pre.h, auto_NNN.c,
functions.tsv (address, status, reason), convs.tsv (register parameters of every prototype used)."""
import argparse, json, os, re, subprocess, sys, glob, hashlib
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
REBUILD = os.path.join(HERE, '..', 'rebuild')

BLOCK = [
    (r'\bunaff_(?!FS_OFFSET\b)\w+', 'unaffected register'), (r'\bextraout_\w+', 'extra output register'),
    # (in_stack_ffff...: below the frame, a slot of the outgoing arguments never written, garbage the original
    # passes on, e.g. the first field of a struct built on the stack for 0x4909E0: its declaration as a local is as
    # good; above the frame it is a parameter the prototype lacks)
    (r'\bin_stack_(?!ff)\w+', 'stack outside the frame'), (r'\bin_[A-Z]{2,4}\b', 'register input'),
    (r'\bin_ST\d\b', 'x87 register input (a value left on the FPU stack the decompiler lost track of)'),
    (r'WARNING: (?!Globals starting|Removing unreachable|Load size|Type propagation|Subroutine does not return)', 'decompiler warning'),
    (r'UNRESOLVED', 'unresolved name'), (r'halt_baddata|halt_unimplemented|software_\w+\(|swi\(', 'bad instruction'),
    (r'\bLOCK\(\)|\bUNLOCK\(\)', 'locked instruction'), (r'_vbase_destructor|__alloca_probe', 'compiler helper'),
    (r'\bin_FS_OFFSET\b', 'TEB access'), (r'\bxRam|\bunique0x', 'unmapped storage'),
    (r'\.\.\.\)', 'varargs'), (r'\bfloat10\s*\*', 'pointer to float10 (10 bytes in the decompiler, 8 in C)'), (r'\bCONCAT\d{3,}|\bSUB\d{3,}', 'wide value'),
]


def load_protos(path):
    p, imports = {}, set()
    for l in open(path, encoding='utf-8'):
        q = l.rstrip('\n').split('\t')
        if len(q) < 6:
            continue
        a, cc, custom, ret, params, varargs = q[:6]
        plist = [x.rsplit(' ', 1) for x in params.split(',') if x.strip()] if params else []
        storage = q[7].split(',') if len(q) > 7 and q[7] else []
        p[int(a, 16)] = [cc, custom == 'true', ret, plist, varargs == 'true', storage]
        if len(q) > 6 and q[6] == 'import':
            imports.add(int(a, 16))
    return p, imports


REG_ORDER = ['ECX', 'EAX', 'EDX', 'EBX', 'ESI', 'EDI']
WIDE = {'double', 'longlong', 'ulonglong', 'undefined8', 'qword', 'float10'}
machine = {}       # addr -> (register inputs, bytes popped by ret) from symbols/<game>_functions.tsv
ebp_in = {}        # functions that read EBP before setting it (funclets using their caller's frame)
convs = {}         # addr -> (registers in parameter order, ret pop) of the prototypes as written out


import_args = {}    # IAT slot -> argument bytes callers remove after calling it (tools/importargs.py)
stack_slots = {}    # addr -> stack slots the machine code uses (tools/stackparams.py, exact ones only)
fsize = {}          # addr -> bytes of machine code
# dwords of the objects the decompiler addresses in the outgoing arguments (MSVC 8 std::string: 28 bytes)
OBJ_DWORDS = {'_Demangler_std_basic_string_char_struct_std__char_traits_char__class_std__allocator_char___': 7,
              'float': 1, 'undefined4': 1, 'int': 1, 'uint': 1, 'undefined8': 2, 'double': 2, 'longlong': 2}


def call_returns(a):
    """the addresses right after the calls of the function at a"""
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    try:
        code = image[0].read(a, fsize.get(a, 0))
    except Exception:
        return set()
    return {i.address + i.size for i in md.disasm(code, a) if i.mnemonic == 'call'}


def load_machine(path):
    for l in open(path):
        if l.startswith('#'):
            continue
        q = l.rstrip('\n').split('\t')
        machine[int(q[0], 16)] = (set(x for x in q[2].split(',') if x and x != 'EBP'), None if q[3] == '?' else int(q[3] or 0))
        fsize[int(q[0], 16)] = int(q[1])
        if 'EBP' in q[2].split(','):
            ebp_in[int(q[0], 16)] = {'EBP'}
    ia = path.replace('_functions.tsv', '_importargs.tsv')
    if os.path.exists(ia):
        for l in open(ia):
            q = l.rstrip('\n').split('\t')
            if l[0] != '#':
                import_args[int(q[0], 16)] = (int(q[1]), int(q[3]) if len(q) > 3 else 0)
    sp = path.replace('_functions.tsv', '_stackparams.tsv')
    if os.path.exists(sp):
        for l in open(sp):
            q = l.rstrip('\n').split('\t')
            if l[0] != '#' and q[2] == 'exact':
                stack_slots[int(q[0], 16)] = int(q[1])


def fit_convention(a, pr):
    """Make the decompiler's prototype agree with the machine code (register inputs found by liveness, the
    bytes ret pops).  LTCG gave many functions conventions of their own: those are written as cdecl with the
    register parameters first, and build.py makes adapters and shims from the register list kept in convs.
    Returns None or the reason the prototype does not fit."""
    cc, custom, ret, plist, va, storage = pr
    if a not in machine:
        return 'no machine-code facts'
    if len(storage) != len(plist):
        return 'parameter storage unknown'
    regs_in, pop = machine[a]
    if pop is None:
        return 'ret pop unknown (no ret found)'
    regs = [s for s in storage if s != 'stack']
    if storage[:len(regs)] != regs:
        return 'register parameter after a stack parameter'
    if len(set(regs)) != len(regs) or not set(regs) <= set(REG_ORDER):
        return 'odd register storage'
    if not regs_in <= set(regs):
        return 'reads registers the prototype lacks (%s)' % ','.join(sorted(regs_in - set(regs)))
    stack = sum(8 if t.strip() in WIDE else 4 for (t, _), s in zip(plist, storage) if s == 'stack')
    if pop == 0 and stack_slots.get(a, 0) * 4 > stack:
        return 'stack parameters the decompiler missed'
    native = {'__cdecl': ([], 0), '__stdcall': ([], stack), '__thiscall': (['ECX'], stack),
              '__fastcall': (['ECX', 'EDX'][:len(regs)], stack)}.get(cc)
    if not custom and native and native[0] == regs and native[1] == pop and not va:
        convs[a] = (regs, pop)
        return None
    if cc not in native_ok and not custom:
        return 'unknown calling convention'
    if va:
        return 'varargs with registers'
    if pop not in (0, stack) or (stack != 4 * (len(storage) - len(regs))):
        return 'stack parameters do not fit the ret'
    pr[0], pr[1] = '__cdecl', True
    convs[a] = (regs, pop)
    return None


native_ok = ('__cdecl', '__stdcall', '__thiscall', '__fastcall')


FPU_ARGS = {'_CIsin': 1, '_CIcos': 1, '_CItan': 1, '_CIsqrt': 1, '_CIatan': 1, '_CIasin': 1, '_CIacos': 1,
            '_CIexp': 1, '_CIlog': 1, '_CIlog10': 1, '_CIsinh': 1, '_CIcosh': 1, '_CItanh': 1,
            '_CIpow': 2, '_CIatan2': 2, '_CIfmod': 2}
fpu_thunks = {}    # 'jmp [import]' thunk of an x87 intrinsic -> (name, arguments): ghidra/FpuIntrinsics.java
ftols = {}         # the runtime's float to integer conversions of ST0 (tools/crtfuncs.py) -> C result type
icalls = {}        # indirect call address -> (convention, stack arguments, result) of ghidra/ICallOverride.java


def matching(code, i):
    """index of the parenthesis closing the one at code[i]"""
    depth = 0
    for j in range(i, len(code)):
        if code[j] == '(':
            depth += 1
        elif code[j] == ')':
            depth -= 1
            if depth == 0:
                return j
    return -1


def split_args(text):
    out, depth, cur = [], 0, ''
    for ch in text:
        if ch in '([':
            depth += 1
        elif ch in ')]':
            depth -= 1
        if ch == ',' and depth == 0:
            out.append(cur.strip()); cur = ''
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def rewrite_icalls(code, floats=None):
    """'(ICALL_A*E)(args)' from AutoExport -> a call of E through a function pointer of the prototype written
    for the call at A (its convention passes the object in ECX for __thiscall); innermost calls first.  floats:
    call address -> indices of the arguments that are floats (AutoExport.java icallfloat), typed float"""
    for m in reversed(list(re.finditer(r'\(ICALL_([0-9A-F]{8})\*', code))):
        a = int(m.group(1), 16)
        if a not in icalls:
            return None, 'indirect call without a prototype'
        cc, nstack, ret = icalls[a]
        close = matching(code, m.start())
        k = close + 1
        while k < len(code) and code[k] in ' \n':
            k += 1
        if close < 0 or k >= len(code) or code[k] != '(':
            return None, 'indirect call not understood'
        end = matching(code, k)
        args = split_args(code[k + 1:end])
        params = (['void *'] if cc == '__thiscall' else []) + ['undefined4'] * nstack
        if len(args) != len(params):
            return None, 'indirect call with %d arguments, %d in its prototype' % (len(args), len(params))
        for x in (floats or {}).get('%08X' % a, '').split(','):
            if x:
                if int(x) >= len(params) or params[int(x)] != 'undefined4':
                    return None, 'float argument of an indirect call not on the stack'
                params[int(x)] = 'float'
        callee = code[m.end():close]
        code = code[:m.start()] + '((%s (%s *)(%s))(%s))(%s)' % (
            ret, cc, ', '.join(params) or 'void', callee, ', '.join(args)) + code[end + 1:]
    return code, None


def has_indirect_call(code):
    """a call through a computed pointer: '(*...)(' or '(**...)(' with the parentheses balanced"""
    for m in re.finditer(r'\(\*', code):
        depth = 0
        i = m.start()
        while i < len(code):
            if code[i] == '(':
                depth += 1
            elif code[i] == ')':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        j = i + 1
        while j < len(code) and code[j] in ' \n':
            j += 1
        if j < len(code) and code[j] == '(':
            return True
    return False


def cc_word(cc, custom):
    if custom:
        return '__cdecl'
    return {'__thiscall': '__thiscall', '__fastcall': '__fastcall', '__stdcall': '__stdcall', '__cdecl': '__cdecl'}.get(cc)


def wide_ret(ret):
    """An undefined result narrower than a register is usually the decompiler not knowing: the callers of
    many functions use all of EAX, so declare it as the whole register."""
    return 'undefined4' if ret in ('undefined', 'undefined1', 'undefined2', 'undefined3') else ret


def def_ret(ret):
    """The result type of a generated definition: one narrower than a register is returned as the whole register,
    extended by value.  The original code set all of EAX ('mov eax, 5') and its callers may test all of it, while a
    C function returning char sets only AL: 0x480020 (where a point lies against a segment, typed char) left
    garbage in the upper bytes, its callers' 'test eax, eax' went wrong and houses lost their collision.  Callers
    that read only AL see the same value.  (Declarations for callers keep the narrow type: an original function may
    leave the upper bytes undefined.)"""
    if ret in ('char', 'short', 'sbyte'):
        return 'int'
    if ret in ('bool', 'byte', 'uchar', 'ushort', 'word', 'undefined1', 'undefined2', 'undefined3'):
        return 'unsigned int'
    return wide_ret(ret)


def proto_text(name, pr):
    cc, custom, ret, plist, va = pr[:5]
    ret = wide_ret(ret)
    w = cc_word(cc, custom)
    if w is None:
        return None
    ps = []
    for i, (t, n) in enumerate(plist):
        ps.append('%s p%d' % (t, i))
    if va:
        ps.append('...')
    return '%s %s %s(%s)' % (ret, w, name, ', '.join(ps) if ps else 'void')


STACKVAR = re.compile(r'^(\s+)([A-Za-z_][\w ]*?)\s*(\**)\s*\b((?:local|[a-zA-Z]+Stack)_([0-9a-f]+)(?:_\d+)?)\s*(\[\d+\])?;\s*$')


def stack_frame(body):
    """declarations of local_X / xStack_X at the top of the body -> macros over gh_frame; returns (body, names)"""
    lines = body.split('\n')
    decl, i = [], 1
    while i < len(lines) and lines[i].strip():
        m = STACKVAR.match(lines[i])
        if m:
            decl.append((i, m))
        i += 1
    if not decl:
        return body, []
    top = max(int(m.group(5), 16) for _, m in decl)
    if top > 0x100000:
        return None, 'stack frame too large'
    out, extra_names = [], []
    for _, m in decl:
        t, ptr, name, off, dim = m.group(2).strip(), m.group(3), m.group(4), int(m.group(5), 16), m.group(6)
        at = '(gh_frame + %d)' % (top - off)
        if dim:
            out.append('#define %s (*(%s %s(*)%s)%s)' % (name, t, ptr, dim, at))
        else:
            out.append('#define %s (*(%s %s*)%s)' % (name, t, ptr, at))
        # '_local_4': the decompiler's name for the dword at the variable, written over it and the bytes after
        # (0x4740C0 '_local_4 = CONCAT31(uStack_3, 2)')
        if re.search(r'\b_%s\b' % name, body):
            out.append('#define _%s (*(unsigned int *)%s)' % (name, at))
            extra_names.append('_' + name)
    drop = set(i for i, _ in decl)
    rest = [l for k, l in enumerate(lines) if k not in drop]
    rest.insert(1, '  unsigned char gh_frame[%d] __attribute__((aligned(16)));' % top)
    return '\n'.join([rest[0]] + out + rest[1:]), [m.group(4) for _, m in decl] + extra_names


def body_of(code):
    i = code.find('{')
    if i < 0:
        return None
    return code[i:]


symaddr = {}
symname = {}
ambiguous = set()   # names given to more than one address


def add_sym(name, addr):
    if symaddr.setdefault(name, addr) != addr:
        ambiguous.add(name)
rets = {}
image = [None]      # the PE of the game (exception tables)
eax_used = set()    # functions whose callers use EAX after the call (tools/retlive.py)


def catches(handler):
    """True unless handler is the frame handler stub of a C++ function without try blocks (only destructors to
    run): 'mov eax, FuncInfo; jmp __CxxFrameHandler3', possibly after a GS cookie check.  Dropping the
    registration of a frame that catches would lose the catch."""
    pe = image[0]
    try:
        code = pe.read(handler, 0x30)
    except Exception:
        return True
    for i in range(len(code) - 5):
        if code[i] == 0xB8:
            fi = int.from_bytes(code[i + 1:i + 5], 'little')
            try:
                magic = pe.u32(fi)
            except Exception:
                continue
            if magic in (0x19930520, 0x19930521, 0x19930522):
                return pe.u32(fi + 12) != 0          # nTryBlocks
    return True


def convert(f, protos, skip, imports, impnames):
    a = int(f['a'], 16)
    if a in skip:
        return None, 'hand-decompiled'
    code = f['code']
    if f.get('floatmix'):
        return None, 'float and integer bits mixed (%s)' % f['floatmix'].split(' at ')[0]
    # a tail jump to an import ('jmp [slot]' ending 0x4206B0): the decompiler warns that it is no switch it can
    # recover and calls the import with its prototype instead, which is what the jump does
    def import_jump(m):
        try:
            b = image[0].read(int(m.group(1), 16), 6)
        except Exception:
            return m.group(0)
        if b[:2] == b'\xff\x25' and int.from_bytes(b[2:6], 'little') in image[0].imports:
            return ''
        return m.group(0)
    code = re.sub(r'/\* WARNING: Could not recover jumptable at 0x([0-9a-f]+)\. Too many branches \*/\s*'
                  r'/\* WARNING: Treating indirect jump as call \*/', import_jump, code)
    for pat, why in BLOCK:
        if re.search(pat, code):
            return None, why
    # a call's return address as a value: the decompiler lost the stack depth and took the pushes of the calls for
    # arguments of a later one (0x475440 'uVar5 = 0x47552f' passed on to 0x475330 with a vector by value)
    rets_here = call_returns(a)
    if any(int(x, 16) in rets_here for x in re.findall(r'\b0x([0-9a-f]{6,8})\b', code)):
        return None, 'return address as a value (stack depth lost)'
    # comments before the definition (the demangled name of an exported function, its own signature with '(void)'
    # that the parameter parsing would take for the definition's), once the warnings among them have been seen
    code = re.sub(r'^(?:\s*/\*.*?\*/)+', '', code, flags=re.S)
    # a callee that reads EBP as the frame of its caller (a funclet: 0x5E4197, the CRT's eh vector constructor
    # iterator, calls 0x5E41E4, which tests [ebp-20h]): no C function keeps the original frame in EBP
    for c in f['callees']:
        if 'EBP' in ebp_in.get(int(c, 16), ()):
            return None, 'callee %s reads the caller\'s EBP' % c
    code, why = rewrite_icalls(code, f.get('icallfloat'))
    if code is None:
        return None, why
    if has_indirect_call(code):
        return None, 'indirect call'
    pr = protos.get(a)
    if not pr:
        return None, 'no prototype'
    why = fit_convention(a, pr)
    if why:
        return None, why
    head = proto_text('f_%08X' % a, pr)
    if head is None:
        return None, 'unknown calling convention'
    body = body_of(code)
    if body is None:
        return None, 'no body'
    # parameter names of the definition: the decompiler's names
    names = re.match(r'[^(]*\((.*?)\)\s*\{', code.replace('\n', ' '), re.S)
    params = []
    if names:
        raw = names.group(1).strip()
        if raw and raw != 'void':
            params = [x.strip() for x in raw.split(',')]
    cc, custom, ret, plist, va = pr[:5]
    if va:
        return None, 'varargs'
    if len(params) != len(plist):
        return None, 'parameter count differs from the prototype'
    if ret.startswith('undefined') and not re.search(r'\breturn\s+[^;\s]', re.sub(r'/\*.*?\*/', '', body, flags=re.S)):
        ret = 'void'               # the decompiler guessed a result that the function never sets
    if ret == 'void' and a in eax_used:
        return None, 'callers use EAX, the decompiler found no result'
    rets[a] = ret
    head = '%s %s f_%08X(%s)' % (def_ret(ret), cc_word(cc, custom), a, ', '.join(params) if params else 'void')
    # namespace prefixes the decompiler printed before calls (templates included)
    body = re.sub(r'(?:\b[A-Za-z_]\w*(?:<[^;{}()]*?>)?\s*::\s*)+(?=sub_[0-9A-F]{8})', '', body)
    # the SEH frame of C++ functions (fs:[0], printed as a global at FFDFF000): our frame layout differs, so the
    # registration is dropped; an exception then passes through without running this function's destructors
    # the address of a symbol is printed as &Class::name: our ((T *)G_X) already is that address
    # (((T *)&G_X) when the same global is also used as a value; T the element type where the decompiler counts
    # elements from it, void otherwise: AutoExport.java)
    body = re.sub(r'&?\s*(?:\b[A-Za-z_]\w*(?:<[^;{}()]*?>)?\s*::\s*)*(\(\([\w ]+(?:\s*\*)+\)&?G_[0-9A-F]{8}\))', r'\1', body)
    # (or as unaff_FS_OFFSET, a pointer variable, where the decompiler did not see the segment, or as the TEB's
    # ExceptionList)
    if 'G_FFDFF000' in body or re.search(r'\b(?:unaff_FS_OFFSET|ExceptionList)\b', body):
        hs = re.findall(r'\b(?:pu|pc|p)\w*Stack_\w+\s*=\s*&?\s*(?:&?(?:LAB|FUN)_|\(\([\w ]+(?:\s*\*)+\)G_)([0-9a-fA-F]{8})\b', body)
        if len(hs) != 1:
            return None, 'exception frame without a known handler'
        if catches(int(hs[0], 16)):
            return None, 'catches exceptions'
    body = re.sub(r'\n[^\n;]*\b(?:G_FFDFF000|unaff_FS_OFFSET|ExceptionList)\b[^\n;]*;', '\n', body)

    # vftable of the function's own class
    own = symname.get(a, '')
    if '::' in own:
        cls = own.rsplit('::', 1)[0]
        # (not a field 'x.vftable' or 'p->vftable', which the decompiler may break across lines)
        body = re.sub(r'(?<![\w:.>])(vftable(?:_\w+)?)\b',
                      lambda m: m.group(1) if re.search(r'(?:\.|->)\s*$', body[max(0, m.start() - 40):m.start()])
                      else cls + '::' + m.group(1), body)
    # the decompiler's NAN(x) tests x (math.h has NAN as the constant)
    body = re.sub(r'\bNAN\(', 'NAN_CHECK(', body)
    # addresses of stack slots below the frame: an object the decompiler declared nothing for ('&stack0xffffffdc' a
    # TableGet at -0x24, 0x43A970) or a by-value argument built in the outgoing arguments (0x42AF50 copies a string
    # to &stack0xffffff98 and passes in_stack_ffffff98.. on): frame variables at those offsets like local_24
    if re.search(r'\bstack0xff[0-9a-f]{6}\b', body):
        # an object built there and passed on by value must be passed whole: the decompiler gives the callee only
        # the slots it knows of (0x53CD20 has a string written to &stack0xffffff74 by 0x561520 and passes one dword
        # of it to 0x46D380, which takes the string)
        flat = re.sub(r'\s+', ' ', body)
        for m in re.finditer(r'(?:\((\w+) \*\) ?)?&stack0x(ff[0-9a-f]{6})\b', flat):
            off = int(m.group(2), 16)
            if not re.search(r'\bin_stack_%08x\b' % off, flat):
                continue                       # not passed on: an object of the frame (0x43A970)
            need = OBJ_DWORDS.get(m.group(1))
            run = 0
            for r in re.finditer(r'\bin_stack_%08x\b(?:\s*,\s*in_stack_ff[0-9a-f]{6}\b)*' % off, flat):
                n = 0
                for v in re.findall(r'in_stack_(ff[0-9a-f]{6})', r.group(0)):
                    if int(v, 16) != off + 4 * n:
                        break
                    n += 1
                run = max(run, n)
            if need is None or run < need:
                return None, 'object built in the outgoing arguments, passed on in part'
        def at(m):
            return 'local_%x' % (0x100000000 - int(m.group(1), 16))
        body = re.sub(r'\bin_stack_(ff[0-9a-f]{6})\b', at, body)
        undeclared = sorted({at(m) for m in re.finditer(r'\bstack0x(ff[0-9a-f]{6})\b', body)} -
                            set(re.findall(r'\blocal_[0-9a-f]+\b', body)))
        body = re.sub(r'\bstack0x(ff[0-9a-f]{6})\b', at, body)
        body = body.replace('{\n', '{\n' + ''.join('  undefined1 %s;\n' % n for n in undeclared), 1)
    # below-frame stack inputs (garbage of the original): zero, not an uninitialized C variable the optimizer may
    # take liberties with
    body = re.sub(r'^(\s*(?:undefined\d|u?int|uint|float|char|byte|short|ushort|[\w ]+\*+)\s*in_stack_ff\w+);',
                  r'\1 = 0;', body, flags=re.M)
    # stack variables at their original offsets: the decompiler splits buffers and structures into scalars that the
    # original kept side by side (and walks across them with pointers), so all named stack variables become views
    # of one frame array laid out as the original stack frame (local_1c is at -0x1c from the return address)
    body, frame_names = stack_frame(body)
    if body is None:
        return None, frame_names
    # labels keep their names (the address substitution below is for LAB_ used as a value)
    body = re.sub(r'\bgoto\s+(LAB_[0-9a-fA-F]{8})\b', r'goto L\1', body)
    body = re.sub(r'^(\s*)(LAB_[0-9a-fA-F]{8}):', r'\1L\2:', body, flags=re.M)
    # pieces of a variable: v._1_3_ is the 3 bytes at offset 1 of v
    bad = []
    def piece(m):
        var, off, size = m.group(1), int(m.group(2)), int(m.group(3))
        if size not in (1, 2, 3, 4, 8):
            bad.append(m.group(0))
        if size == 3 and re.match(r'\s*=[^=]', body[m.end():m.end() + 3]):
            bad.append(m.group(0))   # a 3-byte store has no C type
        t = {1: 'unsigned char', 2: 'unsigned short', 3: 'unsigned int', 4: 'unsigned int', 8: 'unsigned long long'}.get(size, 'int')
        return '(*(%s *)((char *)&%s + %d))' % (t, var, off)
    body = re.sub(r'\b([A-Za-z_]\w*)\._(\d+)_(\d+)_\b', piece, body)
    if bad:
        return None, 'piece of a variable'
    # void * dereferenced: the decompiler did not know the type of the value (int or float), neither do we
    for t_, n_ in [(x.rsplit(' ', 1) + [''])[:2] for x in params]:
        n_ = n_.lstrip('*')
        if t_.strip() == 'void' and re.search(r'(?<![\w)])\*%s\b' % re.escape(n_), body):
            return None, 'void pointer dereferenced'
    # addresses printed as symbol names
    def addr_ref(m):
        return '((void *)d_%s)' % m.group(2).upper()
    extra = set()
    def sym_ref(m):
        q = m.group(0).lstrip('&').replace(' ', '')
        ad = symaddr.get(q)
        if ad is None or q in ambiguous:
            raise KeyError(q)
        extra.add('%08X' % ad)
        return '((void *)d_%08X)' % ad
    body = re.sub(r'&?\b(LAB|PTR_LAB|PTR_FUN|PTR_DAT|PTR_s|FUN|s_\w+?|u_\w+?)_([0-9a-fA-F]{8})\b', addr_ref, body)
    # the address of untyped data is just an address
    body = re.sub(r'&(?:DAT|UNK)_([0-9a-fA-F]{8})\b(?!\s*[\[.])', lambda m: '((void *)d_%s)' % m.group(1).upper(), body)
    for x in re.findall(r'\(\(void \*\)d_([0-9A-F]{8})\)', body):
        extra.add(x)
    if re.search(r'(?<![\w.>])(DAT_|PTR_|BYTE_|WORD_|DWORD_|UNK_)[0-9a-fA-F]{8}\b', body):
        return None, 'global of unknown type'
    try:
        body = re.sub(r'&?(?:\b[A-Za-z_][\w<>,]*(?:<[^;{}()]*?>)?::)+(?:vftable(?:_\w+)?|vbtable\w*|`[^`]*\'|\w+_meta_ptr)', sym_ref, body)
    except KeyError as e:
        return None, 'unknown symbol %s' % e
    for g in re.findall(r'\bG_([0-9A-F]{8})\b', body):
        ad = int(g, 16)
        if not (0x401000 <= ad < 0x1000000):        # (the headers at 400000 are no section)
            return None, 'segment or out-of-image global'
    for x in re.findall(r'\(\(void \*\)d_([0-9A-F]{8})\)', body):
        extra.add(x)
    if '::' in body:
        return None, 'C++ name left'
    if any(not (0x401000 <= int(x, 16) < 0x1000000) for x in extra):
        return None, 'address outside the image'

    decls = []
    for c in f['callees']:
        ca = int(c, 16)
        if ca in ftols:
            # _ftol2(_sse): the value in ST0 converted towards zero, which C's cast does too
            decls.append('#define sub_%s(x) ((%s)(x))' % (c, ftols[ca]))
            continue
        if ca in fpu_thunks:
            # x87 intrinsic (arguments on the FPU stack): rebuild/rt_support.c puts them there and calls it
            name, n = fpu_thunks[ca]
            decls.append('DECOMP_C double decomp%s(%s);' % (name, ', '.join(['double'] * n)))
            decls.append('#define sub_%s decomp%s' % (c, name))
            continue
        cp = protos.get(ca)
        if not cp:
            return None, 'callee %s without prototype' % c
        if ca in imports:
            if ca not in impnames:
                return None, 'import %s not in the import table' % c
            icc, _, iret, iplist, iva = cp[:5]
            if not iva and ca in import_args:
                ps_ = iplist[1:] if icc == '__thiscall' else iplist[2:] if icc == '__fastcall' else iplist
                have = sum(8 if t.strip() in WIDE else 4 for t, _ in ps_)
                cleaned, pushed = import_args[ca]
                need = 4 * pushed if icc in ('__stdcall', '__thiscall', '__fastcall') else cleaned
                if need > have:
                    return None, 'import %s takes more arguments than its prototype' % c
            w = cc_word(icc, False) or '__cdecl'
            ps = ', '.join(t for t, n in iplist) if iplist else 'void'
            if iva:
                ps += ', ...'
            decls.append('DECOMP_C %s (%s *imp_%s)(%s) __asm__("%s");' % (wide_ret(iret), w, c, ps, impnames[ca]))
            decls.append('#define sub_%s (*imp_%s)' % (c, c))
            continue
        why = fit_convention(ca, cp)
        if why:
            return None, 'callee %s: %s' % (c, why)
        t = proto_text('sub_%s' % c, cp)
        if t is None:
            return None, 'callee %s with unknown calling convention' % c
        decls.append('DECOMP_C %s;' % t)
    for g, info in f['globals'].items():
        parts = info.split('|')
        if int(g, 16) in impnames:
            # an import table slot read as data (a function pointer handed on): the rebuilt exe's loader fills the
            # new import table, not the original slots
            decls.append('DECOMP_C void *gimp_%s __asm__("%s");' % (g, impnames[int(g, 16)]))
            decls.append('#define G_%s (*(void **)&gimp_%s)' % (g, g))
            continue
        decls.append('DECOMP_C char d_%s[];' % g)
        if parts[0] == 'code':
            decls.append('#define G_%s d_%s' % (g, g))
        elif parts[0] == 'ARRAY':
            decls.append('#define G_%s ((%s *)d_%s)' % (g, parts[1], g))
        else:
            decls.append('#define G_%s (*(%s *)d_%s)' % (g, parts[0], g))
            if parts[0] in ('undefined4', 'uint', 'int', 'dword', 'ulong', 'long'):
                # a pointer the decompiler typed as a dword, dereferenced ('*G_006C8C10 + 0xe4', the vftable of
                # a COM object): the load of a dword through it
                # (unary: the decompiler writes a product as 'a * b', a dereference without a space)
                body = re.sub(r'(?<![\w\]])\*G_%s\b' % g, r'(*(undefined4 *)G_%s)' % g, body)
    for key, t in f.get('sized', {}).items():
        decls.append('DECOMP_C char d_%s[];' % key[:8])
        decls.append('#define GV_%s (*(%s *)d_%s)' % (key, t, key[:8]))
    for s in f['strings']:
        decls.append('DECOMP_C char d_%s[];' % s)
        decls.append('#define S_%s d_%s' % (s, s))
    for x in sorted(extra):
        decls.append('DECOMP_C char d_%s[];' % x)
    # macros of this function only (the same global can have another type in another function)
    macros = [d for d in decls if d.startswith('#define')]
    decls = [d for d in decls if not d.startswith('#define')]
    undefs = ['#undef ' + d.split()[1] for d in macros] + ['#undef ' + n for n in frame_names]
    text = '/* @func %08X%s */\n%s\nDECOMP(%08X)\n%s\n%s\n%s\n' % (a, ' custom' if custom else '', '\n'.join(macros), a, head, body.strip(), '\n'.join(undefs))
    return (a, decls, text), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('jsonl'); ap.add_argument('types'); ap.add_argument('outdir')
    ap.add_argument('--exe', required=True, help='the original exe (import names)')
    ap.add_argument('--syms', action='append', default=[], help='symbols.tsv of Ghidra (DumpInfo) or .sym files')
    ap.add_argument('--max', type=int, default=0)
    ap.add_argument('--jobs', type=int, default=os.cpu_count() or 4)
    ap.add_argument('--per-unit', type=int, default=150)
    ap.add_argument('--exclude-range', action='append', default=[], metavar='LO-HI',
                    help='addresses left out (e.g. 401000-420600, the Lua 5.1 library: build it from its sources)')
    ap.add_argument('--icalls', help='call-site prototypes of indirect calls (ghidra/ICallOverride.java output)')
    ap.add_argument('--functions', required=True, help='symbols/<game>_functions.tsv (machine-code register inputs)')
    a = ap.parse_args()
    load_machine(a.functions)
    if a.icalls:
        for l in open(a.icalls):
            q = l.rstrip('\n').split('\t')
            if l[0] != '#' and len(q) == 4:
                icalls[int(q[0], 16)] = (q[1], int(q[2]), q[3])
    rl = a.functions.replace('_functions.tsv', '_retlive.tsv')
    if os.path.exists(rl):
        eax_used.update(int(l, 16) for l in open(rl) if l.strip() and l[0] != '#')
    os.makedirs(a.outdir, exist_ok=True)
    protos, imports = load_protos(a.jsonl + '.protos')
    for fn in a.syms:
        for l in open(fn, encoding='utf-8'):
            if l.startswith('#') or not l.strip():
                continue
            if '\t' in l:
                q = l.rstrip('\n').split('\t')
                try:
                    add_sym(q[1].replace(' ', ''), int(q[0], 16))
                except ValueError:
                    pass
            else:
                q = l.split('#')[0].split(None, 2)
                if len(q) == 3 and q[0] != 'SLOT':
                    add_sym(q[2].strip().replace(' ', ''), int(q[0], 16))
                    if q[1] == 'f':
                        symname[int(q[0], 16)] = q[2].strip()
    sys.path.insert(0, HERE)
    from pe import PE
    from crtfuncs import ftol_kind
    pe = PE(a.exe)
    image[0] = pe
    # funclets: functions that address memory through EBP before setting it
    import capstone
    from capstone import x86 as cx
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    for fa in list(ebp_in):
        ebp_in.pop(fa)
        try:
            for i in md.disasm(pe.read(fa, 32), fa):
                if any(o.type == cx.X86_OP_MEM and o.mem.base == cx.X86_REG_EBP for o in i.operands):
                    ebp_in[fa] = {'EBP'}
                    break
                if cx.X86_REG_EBP in i.regs_access()[1] or i.mnemonic in ('push', 'call', 'ret', 'jmp') or \
                        i.mnemonic.startswith('j'):
                    break
        except Exception:
            pass
    for fa in machine:
        try:
            b = pe.read(fa, 6)
        except Exception:
            continue
        if b[:2] == b'\xff\x25':
            slot = int.from_bytes(b[2:6], 'little')
            if slot in pe.imports and pe.imports[slot][1] in FPU_ARGS:
                fpu_thunks[fa] = (pe.imports[slot][1], FPU_ARGS[pe.imports[slot][1]])
        k = ftol_kind(pe.read(fa, 32))
        if k:
            ftols[fa] = k
    impnames = {}
    for addr, (dll, name) in pe.imports.items():
        impnames[addr] = ('__imp_' + name) if name.startswith('?') else ('__imp__' + name)
    # functions already written by hand
    skip = set()
    for fn in glob.glob(os.path.join(REBUILD, 'src', '**', '*.c*'), recursive=True):
        for m in re.finditer(r'DECOMP\(\s*([0-9A-Fa-f]{8})\s*\)', open(fn, encoding='utf-8').read()):
            skip.add(int(m.group(1), 16))
    pre = os.path.join(a.outdir, 'auto_pre.h')
    types = open(a.types, encoding='utf-8').read()
    # Ghidra's own names for a few base types
    types = types.replace('float10 ', 'double ')
    with open(pre, 'w', encoding='utf-8') as f:
        f.write('/* generated by tools/autodecomp.py */\n#pragma once\n#include "ghidra_prelude.h"\n')
        f.write(types)
    inc = ['-I', os.path.abspath(os.path.join(REBUILD, 'include')), '-I', os.path.abspath(a.outdir)]
    cflags = ['--target=i686-pc-windows-msvc', '-x', 'c', '-std=gnu11', '-fms-extensions', '-ffreestanding',
              '-fno-builtin', '-w', '-Wno-error=int-conversion', '-Wno-error=incompatible-pointer-types',
              '-Wno-error=incompatible-function-pointer-types', '-Wno-error=int-to-pointer-cast',
              '-Wno-error=return-type'] + inc
    pch = pre + '.pch'
    r = subprocess.run(['clang'] + cflags[:1] + ['-x', 'c-header', '-std=gnu11', '-fms-extensions', '-ffreestanding',
                        '-w'] + inc + [pre, '-o', pch], capture_output=True, text=True)
    if r.returncode:
        sys.stderr.write(r.stderr[:4000]); sys.exit('the types header does not compile')
    funcs = [json.loads(l) for l in open(a.jsonl, encoding='utf-8')]
    if a.max:
        funcs = funcs[:a.max]
    status = {}
    cands = []
    ranges = [tuple(int(x, 16) for x in r.split('-')) for r in a.exclude_range]
    for f in funcs:
        if any(lo <= int(f['a'], 16) < hi for lo, hi in ranges):
            status[f['a']] = ('rejected', 'excluded range')
            continue
        res, why = convert(f, protos, skip, imports, impnames)
        if res is None:
            status[f['a']] = ('rejected', why)
        else:
            cands.append(res)
    tmp = os.path.join(a.outdir, 'tmp')
    os.makedirs(tmp, exist_ok=True)

    def check(c):
        addr, decls, text = c
        src = os.path.join(tmp, 'f_%08X.c' % addr)
        open(src, 'w', encoding='utf-8').write('#include "auto_pre.h"\n' + '\n'.join(decls) + '\n' + text)
        r = subprocess.run(['clang'] + cflags + ['-include-pch', pch, '-fsyntax-only', src], capture_output=True, text=True)
        if r.returncode == 0:
            os.remove(src)          # the ones that fail stay in tmp/ to be looked at
        if r.returncode:
            err = next((l for l in r.stderr.splitlines() if 'error' in l), 'error')
            return addr, err.split('error:')[-1].strip()[:120]
        return addr, None
    ok = []
    with ThreadPoolExecutor(a.jobs) as ex:
        for (addr, err), c in zip(ex.map(check, cands), cands):
            if err:
                status['%08X' % addr] = ('compile error', err)
            else:
                ok.append(c)
                status['%08X' % addr] = ('compiled', '')
    for old in glob.glob(os.path.join(a.outdir, 'auto_*.c')):
        os.remove(old)
    ok.sort()
    n = 0
    for i in range(0, len(ok), a.per_unit):
        group = ok[i:i + a.per_unit]
        decls = []
        seen = set()
        for _, d, _ in group:
            for x in d:
                if x not in seen:
                    seen.add(x); decls.append(x)
        with open(os.path.join(a.outdir, 'auto_%03d.c' % n), 'w', encoding='utf-8') as f:
            f.write('/* generated by tools/autodecomp.py from Ghidra output - not reviewed */\n#include "auto_pre.h"\n')
            f.write('\n'.join(decls) + '\n\n')
            f.write('\n'.join(t for _, _, t in group))
        n += 1
    import shutil
    shutil.copy(a.jsonl + '.protos', os.path.join(a.outdir, 'protos'))
    with open(os.path.join(a.outdir, 'convs.tsv'), 'w') as f:
        f.write('# address\tregister parameters in order\tret pop bytes (prototypes as the generated code uses them)\n')
        for k in sorted(convs):
            f.write('%08X\t%s\t%d\n' % (k, ','.join(convs[k][0]), convs[k][1]))
    with open(os.path.join(a.outdir, 'rets.tsv'), 'w') as f:
        for k in sorted(rets):
            f.write('%08X\t%s\n' % (k, rets[k]))
    with open(os.path.join(a.outdir, 'functions.tsv'), 'w') as f:
        for k in sorted(status):
            f.write('%s\t%s\t%s\n' % (k, status[k][0], status[k][1]))
    import collections
    c = collections.Counter(v[0] for v in status.values())
    print('functions: %s; %d units' % (dict(c), n))
    rc = collections.Counter(v[1] for v in status.values() if v[0] != 'compiled')
    for k, v in rc.most_common(15):
        print('  %5d %s' % (v, k))


if __name__ == '__main__':
    main()
