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
    (r'WARNING: (?!Globals starting|Removing unreachable|Load size|Type propagation|Subroutine does not return|'
     r'Function: \w+ replaced with injection: decomp_)', 'decompiler warning'),
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
BYVALUE = {'_decomp_StrByValue': 28}     # objects passed by value (ghidra/ByValueParams.java)


def slot_bytes(t):
    t = t.strip()
    return BYVALUE.get(t, 8 if t in WIDE else 4)
machine = {}       # addr -> (register inputs, bytes popped by ret) from symbols/<game>_functions.tsv
ebp_in = {}        # functions that read EBP before setting it (funclets using their caller's frame)
convs = {}         # addr -> (registers in parameter order, ret pop) of the prototypes as written out


import_args = {}    # IAT slot -> argument bytes callers remove after calling it (tools/importargs.py)
stack_slots = {}    # addr -> stack slots the machine code uses (tools/stackparams.py, exact ones only)
fsize = {}          # addr -> bytes of machine code
SYSTEM_DLLS = {'KERNEL32.DLL', 'USER32.DLL', 'GDI32.DLL', 'ADVAPI32.DLL', 'SHLWAPI.DLL', 'SHELL32.DLL', 'WINMM.DLL',
               'OLE32.DLL', 'VERSION.DLL', 'MSVCR80.DLL', 'MSVCP80.DLL'}
STRUCT_SIZE = {}    # type name -> its size (the types header's static assertions)
TRUNCATED = {}     # structure -> offset of the pad array its declaration ends in (members cut short)
ONE_BYTE = set()    # classes the demangler made 1-byte placeholders (std::string, its _Size_type_nosscl)
noreturn = set()    # functions without a ret or a jump out (they throw: 0x493740): no ret pop to know
never_returns = set()   # the same whatever pop they were given (0x4488D0, a vftable slot's, throws)
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


import_pops = {}    # IAT slot -> bytes the imported function pops (its prototype)
byvalue_offs = {}   # function -> offsets of its string parameters passed by value (symbols/GAME_byvalue.tsv)
_depths = {}
unused_params = {}  # addr -> indices of the parameters its decompiled body never names
call_sites = {}     # function -> {address of a direct call: callee}
icall_pops = {}     # indirect call -> bytes its callee pops (tools/icalls.py), None where unknown


def reg_import_pop(code, p, reg, limit=60):
    """the pop of 'call reg' where reg was last written by 'mov reg, [IAT slot]' (MSVC keeps an import called
    more than once in a register: 0x4822A0 'mov ebx, [std::operator+]; ...; call ebx'), straight back; None
    otherwise"""
    from capstone import x86 as cx
    order = sorted(code)
    k = order.index(p)
    for q in reversed(order[max(0, k - limit):k]):
        i = code[q]
        try:
            w = i.regs_access()[1]
        except Exception:
            return None
        if reg in w:
            o = i.operands
            if i.mnemonic == 'mov' and len(o) == 2 and o[1].type == cx.X86_OP_MEM and not o[1].mem.base and \
                    not o[1].mem.index:
                return import_pops.get(o[1].mem.disp)
            return None
    return None


def stack_depths(a, relative=False):
    """ESP at each instruction of the function at a, as bytes below its return address (negative), from the pops of
    its callees; None where that is not known everywhere (a pop unknown, paths that disagree, ESP set otherwise)"""
    key = (a, relative)
    if key in _depths:
        return _depths[key]
    _depths[key] = None
    import capstone
    from capstone import x86 as cx
    from stackfx import switch_targets
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    try:
        code = {i.address: i for i in md.disasm(image[0].read(a, fsize.get(a, 0)), a)}
    except Exception:
        return None
    def u32(x):
        try:
            return int.from_bytes(image[0].read(x, 4), 'little')
        except Exception:
            return None
    call_sites[a] = {p: i.operands[0].imm for p, i in code.items()
                     if i.mnemonic == 'call' and i.operands[0].type == cx.X86_OP_IMM}
    d, todo = {}, [(a, 0)]
    while todo:
        p, dep = todo.pop()
        while p in code:
            if p in d:
                if d[p] != dep:
                    if os.environ.get('AD_DEBUG'):
                        print('stack_depths %08X: paths disagree at %08X (%d, %d)' % (a, p, d[p], dep))
                    return None
                break
            d[p] = dep
            i = code[p]
            m, ops = i.mnemonic, i.operands
            if m.startswith('ret') or m in ('int3', 'hlt'):
                break
            if m == 'push':
                dep -= 4
            elif m == 'pop':
                dep += 4
            elif m in ('sub', 'add') and ops[0].type == cx.X86_OP_REG and ops[0].reg == cx.X86_REG_ESP:
                if ops[1].type != cx.X86_OP_IMM:
                    return None
                dep += -ops[1].imm if m == 'sub' else ops[1].imm
            elif m == 'lea' and ops[0].type == cx.X86_OP_REG and ops[0].reg == cx.X86_REG_ESP and \
                    ops[1].mem.base == cx.X86_REG_ESP and not ops[1].mem.index:
                dep += ops[1].mem.disp      # 'lea esp, [esp]': an alignment nop (0x50554C)
            elif relative and m == 'and' and ops[0].type == cx.X86_OP_REG and ops[0].reg == cx.X86_REG_ESP:
                pass                        # (an aligned frame: depths from the aligned ESP, right relative to each other)
            elif relative and m in ('leave', 'mov') and (m == 'leave' or i.op_str == 'esp, ebp'):
                break                       # (its epilogue: nothing after it is looked at)
            elif m in ('leave', 'pushal', 'popal', 'pushfd', 'popfd') or (ops and ops[0].type == cx.X86_OP_REG and
                                                                        ops[0].reg == cx.X86_REG_ESP):
                return None
            elif m == 'call':
                op = ops[0]
                if op.type == cx.X86_OP_IMM:
                    pop = machine.get(op.imm, (None, None))[1]
                elif op.type == cx.X86_OP_MEM and not op.mem.base and not op.mem.index:
                    pop = import_pops.get(op.mem.disp)
                else:
                    ic = icalls.get(p)
                    pop = None if ic is None else 4 * ic[1] if ic[0] in ('__stdcall', '__thiscall', '__fastcall') \
                        else 0
                    if pop is None and op.type == cx.X86_OP_REG:
                        pop = reg_import_pop(code, p, op.reg)
                    if pop is None:
                        pop = icall_pops.get(p)
                if pop is None:
                    if op.type == cx.X86_OP_IMM and op.imm in noreturn:
                        break
                    if os.environ.get('AD_DEBUG'):
                        print('stack_depths %08X: pop unknown at %08X %s %s' % (a, p, m, i.op_str))
                    return None
                dep += pop
            if m == 'jmp':
                op = ops[0]
                if op.type == cx.X86_OP_IMM and op.imm in code:
                    p = op.imm
                    continue
                for t in switch_targets(i, u32, a, a + fsize.get(a, 0)):
                    todo.append((t, dep))
                break
            if m.startswith('j') or m.startswith('loop'):
                if ops[0].type == cx.X86_OP_IMM:
                    todo.append((ops[0].imm, dep))
            p = i.address + i.size
    _depths[key] = d
    return d


def vararg_counts(a, slot):
    """the argument counts of the calls of the import slot in the function at a, from the 'add esp, N' after each
    (calls without one left out)"""
    import capstone
    from stackfx import cleanup_after
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    try:
        code = {i.address: i for i in md.disasm(image[0].read(a, fsize.get(a, 0)), a)}
    except Exception:
        return set()
    out = set()
    for p, i in code.items():
        if i.mnemonic == 'call' and i.op_str == 'dword ptr [0x%x]' % slot:
            n = cleanup_after(code.get, p + i.size)
            if n > 0:
                out.add(n // 4)
    return out


def outgoing_mismatch(a, code):
    """why the text passes something else than the slot a pointer to the outgoing arguments was built in, or None:
    'mov R, esp' hands a call (the builder) a pointer to a slot a later call (the consumer) takes as an argument;
    the consumer's argument in the text must name what the builder's does"""
    import capstone
    from capstone import x86 as cx
    dm = stack_depths(a, relative=True)
    if dm is None:
        if os.environ.get('AD_DEBUG'):
            print('outgoing %08X: no depths' % a)
        return None
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    try:
        ins = list(md.disasm(image[0].read(a, fsize.get(a, 0)), a))
    except Exception:
        return None
    def text_calls(c):
        out = []
        for cm in re.finditer(r'\bsub_%08X\s*\(' % c, code):
            depth, q = 1, cm.end()
            while q < len(code) and depth:
                depth += {'(': 1, ')': -1}.get(code[q], 0)
                q += 1
            out.append(split_args(code[cm.end():q - 1]))
        return out
    for k, i in enumerate(ins):
        if not (i.mnemonic == 'mov' and i.op_str.endswith(', esp') and
                i.op_str.split(',')[0] in ('eax', 'ecx', 'edx', 'ebx', 'esi', 'edi')) or i.address not in dm:
            continue
        reg, slot = i.op_str.split(',')[0], dm[i.address]
        builder = consumer = None
        pushes = 0
        for j in ins[k + 1:k + 24]:
            if j.mnemonic.startswith('ret') or j.mnemonic.startswith('j'):
                break
            if j.mnemonic == 'push':
                pushes += 1
                if builder is None and j.op_str == reg:
                    builder = ['stack', pushes]
                continue
            if j.mnemonic == 'call':
                if j.operands[0].type != cx.X86_OP_IMM or j.address not in dm:
                    break
                c, dc = j.operands[0].imm, dm[j.address]
                if builder is not None and builder[0] == 'stack' and len(builder) == 2:
                    builder = (c, 'stack', pushes - builder[1])          # its stack argument index
                elif builder is None and reg == 'ecx':
                    builder = (c, 'this', 0)
                elif builder is not None and len(builder) == 3:
                    regs, pop = machine.get(c, (set(), None))
                    nstack = stack_slots.get(c, (pop or 0) // 4)
                    if dc <= slot < dc + 4 * nstack:
                        consumer = (c, (slot - dc) // 4, len(regs))
                    break
                if builder is None:
                    break
                continue
            if j.operands and j.operands[0].type == cx.X86_OP_REG and j.op_str.split(',')[0] == reg and \
                    j.mnemonic not in ('push', 'cmp', 'test') and builder is None:
                break                               # the pointer overwritten before any use
        if not builder or len(builder) != 3 or not consumer or consumer[0] in byvalue_offs:
            continue
        bc, kind, bk = builder
        bregs = len(machine.get(bc, (set(), None))[0])
        cc, ck, cregs = consumer
        names = set()
        for args in text_calls(bc):
            idx = 0 if kind == 'this' else bregs + bk
            if idx < len(args):
                names.update(re.findall(r'\b(?:local_[0-9a-f]+|\w*Stack_[0-9a-f]+|stack0x[0-9a-f]+)\b', args[idx]))
        if not names:
            continue
        # (one slot under its other names: stack0xffffffd8 written, in_stack_ffffffd8 read, 0x48EB50)
        for n in list(names):
            m = re.fullmatch(r'stack0x(ff[0-9a-f]{6})', n)
            if m:
                names.update(['in_stack_' + m.group(1), 'local_%x' % (0x100000000 - int(m.group(1), 16))])
        calls = text_calls(cc)
        if os.environ.get('AD_DEBUG'):
            print('outgoing %08X: builder %08X arg %s, consumer %08X arg %d: %s' % (a, bc, names, cc, cregs + ck,
                  [x[cregs + ck] if len(x) > cregs + ck else None for x in calls]))
        if calls and not any(len(x) > cregs + ck and any(re.search(r'\b%s\b' % n, x[cregs + ck]) for n in names)
                             for x in calls):
            return 'argument of %08X built in the outgoing arguments, passed as another value' % cc
    return None


def outgoing_object_dwords(a, off):
    """dwords of the object a builds in its outgoing arguments at stack0x<off> ('sub esp, 0xc; mov ecx, esp' or
    'push ecx; mov ecx, esp' with ESP there, then a constructor call): the bytes reserved right before the
    pointer to them is taken; None unless every such place agrees"""
    dm = stack_depths(a)
    if dm is None:
        return None
    import capstone
    from capstone import x86 as cx
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    try:
        ins = list(md.disasm(image[0].read(a, fsize.get(a, 0)), a))
    except Exception:
        return None
    sizes = set()
    for k, i in enumerate(ins):
        if k == 0 or dm.get(i.address) != off - 0x100000000:
            continue
        ops = i.operands
        if not (i.mnemonic in ('mov', 'lea') and len(ops) == 2 and ops[0].type == cx.X86_OP_REG and
                (i.op_str.endswith(', esp') or i.op_str.endswith('[esp]'))):
            continue
        q = k - 1          # (back over what leaves ESP alone: 'sub esp, 0xc; lea edx, [esp + 0x2c]; mov ecx, esp')
        while q > 0 and k - q < 4 and ins[q].mnemonic not in ('push', 'pop', 'call', 'sub', 'add') and \
                cx.X86_REG_ESP not in ins[q].regs_access()[1]:
            q -= 1
        prev = ins[q]
        if prev.mnemonic == 'sub' and prev.op_str.startswith('esp, ') and prev.operands[1].type == cx.X86_OP_IMM:
            sizes.add(prev.operands[1].imm)
        elif prev.mnemonic == 'push':
            sizes.add(4)
        else:
            return None
    if len(sizes) != 1 or min(sizes) % 4:
        return None
    return sizes.pop() // 4


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
    bv = path.replace('_functions.tsv', '_byvalue.tsv')
    if os.path.exists(bv):
        for l in open(bv):
            q = l.rstrip('\n').split('\t')
            if l[0] != '#' and len(q) > 1 and q[1]:
                byvalue_offs[int(q[0], 16)] = sorted(int(x) for x in q[1].split(','))
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
    if pop is None and a not in noreturn:
        return 'ret pop unknown (no ret found)'
    regs = [s for s in storage if s != 'stack']
    if storage[:len(regs)] != regs:
        return 'register parameter after a stack parameter'
    if len(set(regs)) != len(regs) or not set(regs) <= set(REG_ORDER):
        return 'odd register storage'
    if not regs_in <= set(regs):
        return 'reads registers the prototype lacks (%s)' % ','.join(sorted(regs_in - set(regs)))
    stack = sum(slot_bytes(t) for (t, _), s in zip(plist, storage) if s == 'stack')
    if pop is None:             # never returns: what a ret would pop does not matter, the convention's is taken
        pop = stack if cc in ('__stdcall', '__thiscall', '__fastcall') and not custom else 0
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
    # (a string by value is one parameter of 7 slots: 0x46D380)
    wide = sum(slot_bytes(t) - 4 for (t, _), s in zip(plist, storage) if s == 'stack' and t in BYVALUE)
    if pop not in (0, stack) or (stack - wide != 4 * (len(storage) - len(regs))):
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
        # (a result the decompiler uses where ICallOverride.java, deciding before, found none: 0x4DDF10
        # 'iVar5 = (*vf)(obj)' at 0x4DE566; EAX after the call, as the machine code reads it)
        alone = re.search(r'[;{}]\s*$', code[:m.start()]) and re.match(r'\s*;', code[end + 1:])
        if ret == 'void' and not alone:
            ret = 'undefined4'
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
eax_used = set()        # functions whose callers use EAX after the call (tools/retlive.py)
eax_handers = set()     # functions that hand their caller's EAX back (symbols/GAME_eaxin.tsv)


def prologue_handler(a):
    """the SEH handler the prologue registers: 'push -1; push HANDLER; mov eax, fs:[0]' (or 'push fs:[0]'), None
    if the function does not begin so"""
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    try:
        ins = list(md.disasm(image[0].read(a, 48), a))[:12]
    except Exception:
        return None
    last = None
    for i in ins:
        if 'fs:[0]' in i.op_str and (i.mnemonic == 'push' or (i.mnemonic == 'mov' and i.op_str.startswith('eax'))):
            return last
        if i.mnemonic == 'push' and i.op_str.startswith('0x') and int(i.op_str, 16) >= 0x401000:
            last = int(i.op_str, 16)
        elif i.mnemonic in ('call', 'ret', 'jmp') or i.mnemonic.startswith('j'):
            return None
    return None


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
                # try blocks whose every handler is catch (...) { clean up; throw; } (the rollback of the standard
                # library's containers, 276 functions): without an exception the function never enters one, with
                # one it goes on to the caller's handler either way; only the clean-up is lost
                n_try, p_try = pe.u32(fi + 12), pe.u32(fi + 16)
                for t in range(n_try):
                    e = p_try + 20 * t
                    for c in range(pe.u32(e + 12)):
                        hd = pe.u32(e + 16) + 16 * c
                        if pe.u32(hd + 4) != 0 or not rethrows(pe.u32(hd + 12)):
                            return True
                return False
    return True


def rethrows(funclet):
    """a catch funclet that throws again ('throw;': _CxxThrowException(0, 0)) before any ret or jmp"""
    import capstone
    pe = image[0]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    throw = {a for a, (d, n) in pe.imports.items() if n == '_CxxThrowException'}
    try:
        code = pe.read(funclet, 0x200)
    except Exception:
        return False
    for i in md.disasm(code, funclet):
        if i.mnemonic == 'call':
            t = i.op_str
            m = re.match(r'dword ptr \[(0x[0-9a-f]+)\]$', t)
            if m and int(m.group(1), 16) in throw:
                return True
            if re.match(r'0x[0-9a-f]+$', t):
                b = pe.read(int(t, 16), 6)
                if b[:2] == b'\xff\x25' and int.from_bytes(b[2:6], 'little') in throw:
                    return True
        if i.mnemonic in ('ret', 'jmp'):
            return False
    return False


FORCE = [False]     # --draft: the soft reasons to reject a function are noted (NOTES) and the text made anyway
NOTES = []


def convert(f, protos, skip, imports, impnames):
    a = int(f['a'], 16)
    if a in skip:
        return None, 'hand-decompiled'
    code = f['code']
    if f.get('floatmix'):
        if not FORCE[0]:
            return None, 'float and integer bits mixed (%s)' % f['floatmix'].split(' at ')[0]
        NOTES.append('float and integer bits mixed (%s)' % f['floatmix'].split(' at ')[0])
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
    # a bool result handed on: the upper bytes of EAX are what the callee left there (0x420BC0 returns std::operator==
    # of strings), which callers never read (they test AL): zero
    code = re.sub(r'\bCONCAT31\(extraout_var(?:_\d+)?\s*,', 'CONCAT31(0,', code)
    # (or the upper bytes of a register a callee left, under the bool computed into its low byte: 0x516880's
    # 'CONCAT31((undefined4)((uint)extraout_EDX >> 8), a == b)', passed as a bool argument)
    # (also those of a callee-saved register the caller left, 0x545400 'CONCAT31((undefined4)((uint)unaff_EBX >> 8),
    # 5)': its byte argument)
    code = re.sub(r'\bCONCAT31\(\s*\(\w+\)\s*\(\s*\(\w+\)\s*(?:extraout|unaff)_E[A-Z]{2}(?:_\d+)?\s*>>\s*8\s*\)\s*,',
                  'CONCAT31(0,', code)
    for v in set(re.findall(r'(?m)^[ \t]*\w+[ \t]+((?:extraout|unaff)_E[A-Z]{2}(?:_\d+)?);$', code)):
        if len(re.findall(r'\b%s\b' % v, code)) == 1:
            code = re.sub(r'(?m)^[ \t]*\w+[ \t]+%s;\n' % v, '', code)
    # the whole stack slot of a parameter narrower than a dword ('_param_3 = 0', a loop counter in the slot of
    # 0x486010's undefined1 param_3): the parameter declared as the dword, its narrow uses cast
    for n in sorted(set(re.findall(r'\b_param_(\d+)\b', code))):
        i = code.find('{')
        hd = re.search(r'([(,]\s*)([A-Za-z_]\w*)(\s+)param_%s(\s*[,)])' % n, code[:i])
        if not hd or hd.group(2) in WIDE or hd.group(2) in BYVALUE or \
                re.search(r'\b_param_%s\s*=\s*CONCAT' % n, code) or re.search(r'(?<![.>\w])param_%s\s*=[^=]' % n, code[i:]):
            continue
        t = hd.group(2)
        body = re.sub(r'(?<![.>\w])param_%s\b' % n, '((%s)param_%s)' % (t, n), code[i:])
        body = re.sub(r'\b_param_%s\b' % n, 'param_%s' % n, body)
        code = code[:hd.start()] + '%s%s%sparam_%s%s' % (hd.group(1), 'uint', hd.group(3), n, hd.group(4)) + \
            code[hd.end():i] + body
    # undefined bytes past where the types header cut a structure short (CConsole's from 0x1059: 0x4426E0's
    # '&this->field_0x1638')
    for v, t in re.findall(r'(?:^|[(,])\s*(_\w+)\s*\*\s*(\w+)\s*(?=[,)])', code[:code.find('{')]) + \
            re.findall(r'(?m)^[ \t]+(_\w+)\s*\*\s*(\w+);$', code):
        if v in TRUNCATED:
            code = re.sub(r'\b%s->field_0x([0-9a-f]+)\b' % t, lambda m: '((unsigned char *)%s)[0x%s]' % (t, m.group(1))
                          if int(m.group(1), 16) >= TRUNCATED[v] else m.group(0), code)
            if v in STRUCT_SIZE:      # ('&this[-1].field_0x1654', 0x4427D0)
                code = re.sub(r'\b%s\[(-?\d+)\]\.field_0x([0-9a-f]+)\b' % t,
                              lambda m: '((unsigned char *)%s)[%d]' % (t, int(m.group(1)) * STRUCT_SIZE[v] +
                                                                     int(m.group(2), 16))
                              if int(m.group(2), 16) >= TRUNCATED[v] else m.group(0), code)
    # a LARGE_INTEGER as a number ('(longlong)local_8', 0x4E41C0): its 8 bytes as one (not QuadPart, a LONGLONG
    # the types header has as double: the timer's frequency read as a double made the menu flicker)
    for v in re.findall(r'(?m)^[ \t]+_winnt_h_LARGE_INTEGER\s+(\w+);$', code):
        code = re.sub(r'\((?:u?longlong|ulonglong|float10|double)\)%s\b(?!\.)' % v,
                      lambda m: m.group(0).replace(v, '*(longlong *)&' + v), code)
    # a switch on a pointer (0x54C6C0's 'switch(param_1)' of an undefined4 *, 0x5952A0's of an HWND): on its value
    for m in set(re.findall(r'\bswitch\((\w+)\)', code)):
        if re.search(r'(?:\*\s*|\b_WinDef_h_H[A-Z]+\s+)%s\s*[;,)]' % m, code[:code.find(')', code.find('{'))]) or \
                re.search(r'(?m)^[ \t]+(?:[A-Za-z_][\w ]*?\s*\*+|_WinDef_h_H[A-Z]+)\s*%s;$' % m, code):
            code = re.sub(r'\bswitch\(%s\)' % m, 'switch((unsigned int)%s)' % m, code)
            code = re.sub(r'\bcase \((?:[\w ]+\*+|_WinDef_h_H[A-Z]+)\)(-?(?:0x[0-9a-f]+|\d+)):', r'case \1:', code)
    # the bits of an array, as in C its address ('BITCAST(float, (auStack_c4))' of a std::string passed as a
    # float parameter, 0x580750: 'lea ecx, [esp + 0x80]; push ecx'; the array whole is of another size)
    arrays = set(re.findall(r'(?m)^[ \t]+[A-Za-z_][\w ]*?[\s*]+(\w+)\s*\[\d+\];$', code))
    code = re.sub(r'\bBITCAST\(([^,()]+), \((\w+)\)\)',
                  lambda m: 'BITCAST(%s, ((void *)%s))' % (m.group(1), m.group(2)) if m.group(2) in arrays
                  else m.group(0), code)
    # a global without a type subscripted ('(&((void *)G_006C7C90))[param_1]', 0x579BA0): the decompiler's
    # undefined1 elements, bytes (all such accesses are 'mov al, byte ptr [eax + 0x6c7c90]')
    code = re.sub(r'\(&\(\(void \*\)(&?G_[0-9A-F]{8})\)\)\[', r'((unsigned char *)\1)[', code)
    # the ST0 result of an indirect call (an override cannot give the decompiler an x87 result, it writes
    # extraout_ST0 where the value is used: 0x426FB0 'call edx; fstp [esp+4]'): the variable is set by the float
    # call right before its first use, in straight code
    if 'extraout_ST0' in code and icalls:
        sites = []
        for m in re.finditer(r'\(ICALL_([0-9A-F]{8})\*', code):
            ic = icalls.get(int(m.group(1), 16))
            close = matching(code, m.start())
            k = close + 1
            while 0 < k < len(code) and code[k] in ' \n':
                k += 1
            if not ic or ic[2] not in ('float', 'double') or close < 0 or k >= len(code) or code[k] != '(' or \
                    not re.search(r'[;{}]\s*(?:/\*[^*]*\*/\s*)*$', code[:m.start()]):
                continue
            end = matching(code, k)
            if end > 0 and re.match(r'\s*;', code[end + 1:]):
                sites.append((m.start(), code.index(';', end) + 1))
        vs = sorted(set(re.findall(r'\bextraout_ST0(?:_\d+)?\b', code)))
        decl = re.compile(r'(?m)^[ \t]*float10[ \t]+(extraout_ST0(?:_\d+)?);$')
        first = {}
        for v in vs:
            uses = [u.start() for u in re.finditer(r'\b%s\b' % v, code)
                    if not decl.match(code, code.rfind('\n', 0, u.start()) + 1)]
            if uses:
                first[v] = uses[0]
        put = {}
        for v, at in first.items():
            prev = [s for s in sites if s[1] <= at]
            if prev and not re.search(r'[{}]|\belse\b', code[prev[-1][1]:at]):
                put[v] = prev[-1]
        if put and len(put) == len(first) == len(set(put.values())):
            for v, (s_, _) in sorted(put.items(), key=lambda x: -x[1][0]):
                code = code[:s_] + '%s = ' % v + code[s_:]
            for v in put:
                code = re.sub(r'\b%s\b' % v, v.replace('extraout_ST0', 'fST0_ret'), code)
    # the 64-bit result of _ftol handed on whole (0x44A4D0 'return CONCAT44(extraout_EDX,(int)fVar1)': the
    # injection decomp_ftol_int keeps EAX only): the float truncated to 64 bits, EDX:EAX as _ftol leaves them
    if 'decomp_ftol_int' in code:
        code = re.sub(r'\bCONCAT44\(extraout_EDX(?:_\d+)?,\(int\)(\w+)\)', r'(ulonglong)(longlong)\1', code)
        for v in set(re.findall(r'(?m)^[ \t]*\w+[ \t]+(extraout_EDX(?:_\d+)?);$', code)):
            if len(re.findall(r'\b%s\b' % v, code)) == 1:
                code = re.sub(r'(?m)^[ \t]*\w+[ \t]+%s;\n' % v, '', code)
    # a local Ghidra declares undefined4 but assigns a pointer and dereferences (0x545400 'local_63c = (int
    # *)sub_0053EA20(); local_63c[1] = ...'): give the declaration that pointer type (same size)
    for v in re.findall(r'(?m)^  undefined4 (\w+);$', code):
        m = re.search(r'\b%s = \((\w+) \*\)' % v, code)
        if m and re.search(r'(\*%s\b|\b%s\[)' % (v, v), code):
            code = re.sub(r'(?m)^  undefined4 %s;$' % v, '  %s *%s;' % (m.group(1), v), code)
    # a register the caller never set, handed as an argument the callee never reads: 0.  Never read by the
    # machine code, not only by the decompiled body (0x42DEE0 'sub_0042DC20(..., unaff_EDI)': the decompiler
    # had the call's two vectors a dword off, lost EDI, the x of the second, and the Furies' spears were not drawn):
    # the parameter's dword at or past every stack slot the callee touches (tools/stackparams.py, exact ones)
    if re.search(r'\bunaff_E[A-Z]{2}\b|\bunaff_retaddr\b', code):
        out = []; last = 0
        for m in re.finditer(r'\b(?:sub|f)_([0-9A-F]{8})\(', code):
            ca = int(m.group(1), 16)
            un = set(unused_params.get(ca, ()))
            cp = protos.get(ca)
            if un and cp and len(cp[5]) == len(cp[3]) and ca in stack_slots:
                off, keep = 0, set()
                for n, ((t, _), st) in enumerate(zip(cp[3], cp[5])):
                    if st == 'stack':
                        if n in un and off // 4 >= stack_slots[ca]:
                            keep.add(n)
                        off += slot_bytes(t)
                un = keep
            else:
                un = set()
            if not un or m.end() < last:
                continue
            j = m.end() - 1; e = matching(code, j)
            if e < 0:
                continue
            args = split_args(code[j + 1:e])
            new = ['0' if n in un and re.fullmatch(r'\s*(?:\(\w+\s*\**\))?\s*unaff_(?:E[A-Z]{2}|retaddr)\s*', x)
                   else x for n, x in enumerate(args)]
            if new != args:
                out.append((j + 1, e, ','.join(new))); last = e
        for b, e, t in reversed(out):
            code = code[:b] + t + code[e:]
        for v in set(re.findall(r'(?m)^[ \t]*\w+[ \t]+\**(unaff_(?:E[A-Z]{2}|retaddr));$', code)):
            if len(re.findall(r'\b%s\b' % v, code)) == 1:
                code = re.sub(r'(?m)^[ \t]*\w+[ \t]+\**%s;\n' % v, '', code)
    xdecl = r'(?m)^[ \t]*\w+[ \t]+extraout_var(?:_\d+)?;\n'
    if not re.search(r'\bextraout_var', re.sub(xdecl, '', code)):
        code = re.sub(xdecl, '', code)
    # a byte stored through a pointer to a class the demangler made a 1-byte placeholder (std::string):
    # 'this_01[0x70] = (_Demangler_..._ )0x1;' (0x45E4D0) assigns a number to a struct in C: the byte
    code = re.sub(r'(?m)^(\s*)(\w+)\[([^\[\]]+)\]\s*=\s*\((_Demangler_\w+)\)\s*(0x[0-9a-fA-F]+|\d+)\s*;',
                  r'\1((unsigned char *)\2)[\3] = (unsigned char)\5;', code)
    # (and a byte variable the decompiler gave such a class, compared with '(class)0x0': 0x51AC00) an unsigned char
    if ONE_BYTE:
        one = '|'.join(sorted(ONE_BYTE, key=len, reverse=True))
        code = re.sub(r'(?m)^(\s*)(?:%s)(\s+\w+\s*;)' % one, r'\1unsigned char\2', code)
        code = re.sub(r'\((?:%s)\)(\s*(?:0x[0-9a-fA-F]+|\d+)\b)' % one, r'(unsigned char)\1', code)
        code = re.sub(r'\*\s*\((?:%s)\s*\*\)' % one, '*(unsigned char *)', code)
        # bytes read or written through a pointer to one ('bVar1 = pbVar2[0x45];'): through an unsigned char *
        for v in set(re.findall(r'(?m)(?:^\s*|[(,]\s*)(?:%s)\s*\*\s*(\w+)\s*[;,)]' % one, code)):
            code = re.sub(r'(?<![\w.>])%s\[' % v, '((unsigned char *)%s)[' % v, code)
    for pat, why in BLOCK:
        if re.search(pat, code):
            if not FORCE[0]:
                return None, why
            NOTES.append(why)
    # a register a callee takes, declared as a local of this function (it is no parameter here): the decompiler
    # lets the callee have this function's own EAX, an uninitialized variable in C (0x547F10 passes 'in_eax' on
    # to 0x4AC7F0, 0x491F50 to 0x491CF0, which then faulted).  Mostly it is an ordinary local the decompiler named
    # after the callee's parameter (0x422160 'in_eax = ExceptionList;', or set in a branch before its use): the
    # compiler's uninitialized-use errors (cflags below) tell the two apart.  Given unset only to functions that
    # merely hand EAX back (eaxin.py) in calls whose result goes unused, it is whatever EAX held, garbage the
    # original passes on and drops: 0 (0x5A9550 to 0x54D350)
    decl, rest = (re.split(r'\n[ \t]*\n', code[code.find('{') + 1:].strip('\n'), 1) + [''])[:2]
    for m in re.finditer(r'(?m)^\s+(?!return\b)[A-Za-z_][\w ]*?\**\s*\b(in_eax\w*)\s*;', decl):
        v = m.group(1)
        uses = [u for u in re.findall(r'(?m)^.*\b%s\b.*$' % v, rest)]
        if uses and all(re.match(r'\s*sub_([0-9A-F]{8})\s*\(.*\);\s*$', u) and
                        int(re.match(r'\s*sub_([0-9A-F]{8})', u).group(1), 16) in eax_handers for u in uses):
            code = re.sub(r'\b%s\b(?!\s*;)' % v, '0', code)
            code = re.sub(r'(?m)^\s+[A-Za-z_][\w ]*?\**\s*\b%s\s*;\n' % v, '', code)
    # a call's return address as a value: the decompiler lost the stack depth and took the pushes of the calls for
    # arguments of a later one (0x475440 'uVar5 = 0x47552f' passed on to 0x475330 with a vector by value)
    rets_here = call_returns(a)
    # a string passed by value that a callee built through a pointer to the outgoing arguments ('lea; push eax;
    # call 0x4638C0; call 0x46D380', 0x50C3C0): the decompiler knows only the first dword written and takes the
    # other six from what was pushed there before, return addresses included; the string is the 28 bytes at the
    # frame variable whose address went to the callee
    def whole(m):
        lines = m.group(0).rstrip('\n').split('\n')
        fields = dict(re.match(r'\s*\w+\.d(\d) = ([^;]*);', l).groups() for l in lines)
        v = re.sub(r'\._0_4_$', '', re.sub(r'^\((?:u?int|undefined4)\)', '', fields.get('0', '')))
        # (a frame variable, or still the slot below the frame: in_stack_fffff8b4 read, &stack0xfffff8b4 passed)
        mv = re.fullmatch(r'(?:local|[a-zA-Z]+Stack)_([0-9a-f]+)', v)
        ms = re.fullmatch(r'in_stack_(ff[0-9a-f]{6})', v)
        if ms:
            v, off = 'stack0x' + ms.group(1), 0x100000000 - int(ms.group(1), 16)
        elif mv:
            off = int(mv.group(1), 16)
        if len(fields) != 7 or not (mv or ms) or off < 28 or not re.search(r'&\s*%s\b' % v, code):
            return m.group(0)
        return '%s%s = *(_decomp_StrByValue *)&%s;\n' % (re.match(r'\s*', lines[0]).group(0), m.group(1), v)
    code = re.sub(r'(?m)^[ \t]*(\w+)\.d\d = [^;\n]*;\n(?:[ \t]*\1\.d\d = [^;\n]*;\n){6}', whole, code)
    # the others: where the string is, from the depth of the stack at the calls of the callee (a copy-constructed
    # string the decompiler gave pieces of other values: 0x4662A0 passes floats and pointers as 0x45C740's string)
    def string_at_call(code):
        dm = stack_depths(a)
        if dm is None:
            return code
        def calls_of(callee):
            """(start, end, args) of the calls of callee in the text, in order"""
            out = []
            for c in re.finditer(r'\bsub_%08X\s*\(' % callee, code):
                depth, q = 1, c.end()
                while q < len(code) and depth:
                    depth += {'(': 1, ')': -1}.get(code[q], 0)
                    q += 1
                out.append((c.start(), q, [x.strip() for x in split_args(code[c.end():q - 1])]))
            return out
        out = []
        for m in re.finditer(r'(?m)^([ \t]*)(\w+)\.d\d = [^;\n]*;\n(?:[ \t]*\2\.d\d = [^;\n]*;\n){6}', code):
            sv = m.group(2)
            c = re.compile(r'\bsub_([0-9A-F]{8})\s*\(').search(code, m.end())
            if not c or ';' in code[m.end():c.start()]:
                continue
            callee = int(c.group(1), 16)
            offs = byvalue_offs.get(callee, [])
            calls = calls_of(callee)
            this = next((x for x in calls if x[0] == c.start()), None)
            if not offs or this is None or sv not in this[2]:
                continue
            k = sum(1 for x in this[2][:this[2].index(sv)] if re.fullmatch(r'str_\d+(?:_\d+)?', x))
            if k >= len(offs):
                continue
            sites = sorted(p for p, t in call_sites.get(a, {}).items() if t == callee and p in dm)
            locs = {dm[p] + offs[k] - 4 for p in sites}
            if len(locs) != 1:
                # the calls in the text in the order of the machine code's, checked on the strings already placed
                if len(calls) != len(sites):
                    continue
                ok = True
                for (cs, ce, args), p in zip(calls, sites):
                    strs = [x for x in args if re.fullmatch(r'str_\d+(?:_\d+)?', x)]
                    if len(strs) <= k:
                        ok = False
                        break
                    w = re.search(r'\b%s = \*\(_decomp_StrByValue \*\)&(?:local_([0-9a-f]+)|stack0x([0-9a-f]{8}));'
                                  % strs[k], code[max(0, cs - 400):cs])
                    if w:
                        at = -int(w.group(1), 16) if w.group(1) else int(w.group(2), 16) - 0x100000000
                        if at != dm[p] + offs[k] - 4:
                            ok = False
                            break
                if not ok:
                    continue
                locs = {dm[sites[[x[0] for x in calls].index(c.start())]] + offs[k] - 4}
            out.append((m.start(), m.end(), '%s%s = *(_decomp_StrByValue *)&stack0x%08x;\n'
                        % (m.group(1), sv, locs.pop() & 0xffffffff)))
        for s_, e_, t in reversed(out):
            code = code[:s_] + t + code[e_:]
        return code
    code = string_at_call(code)
    # a return address the decompiler took for a dword of the outgoing arguments, passed on (0x574ED0: 0x435D90
    # copy-constructs a 12-byte object at &stack0xffffffd8, 0x5735B0 gets in_stack_ffffffd8, in_stack_ffffffdc
    # and 'uVar2 = 0x574efb'): the slot itself, from the depth of the stack at the call and the callee's
    # parameters
    def retaddr_at_call(code):
        rv = {m.group(1) for m in re.finditer(r'(?m)^[ \t]*(\w+) = (?:\([^()]*\))?0x([0-9a-f]{6,8});$', code)
              if int(m.group(2), 16) in rets_here}
        if not rv:
            return code
        dm = stack_depths(a)
        if os.environ.get('AD_DEBUG'):
            print('retaddr %08X: %s, depths %s' % (a, sorted(rv), 'none' if dm is None else len(dm)))
        if dm is None:
            return code
        out = []
        for callee in sorted({int(x, 16) for x in re.findall(r'\bsub_([0-9A-F]{8})\s*\(', code)}):
            pr = protos.get(callee)
            sites = sorted(p for p, t in call_sites.get(a, {}).items() if t == callee and p in dm)
            calls = [(c.start(), c.end() - 1) for c in re.finditer(r'\bsub_%08X\s*\(' % callee, code)]
            if not pr or not sites or pr[4] or len(pr[5]) != len(pr[3]):
                continue
            for n, (cs, j) in enumerate(calls):
                e = matching(code, j)
                if e < 0:
                    continue
                args = split_args(code[j + 1:e])
                if len(args) != len(pr[3]) or not any(x in rv for x in args):
                    continue
                if len({dm[p] for p in sites}) == 1:
                    dep = dm[sites[0]]
                elif len(calls) == len(sites):
                    dep = dm[sites[n]]
                else:
                    continue
                new, off = [], 0
                for x, (t, _), st in zip(args, pr[3], pr[5]):
                    if st == 'stack' and x in rv:
                        d = re.search(r'(?m)^[ \t]*([A-Za-z_][\w ]*?\s*\**)\s*\b%s;$' % x, code)
                        if not d or slot_bytes(t) != 4:
                            break
                        x = '*(%s *)&stack0x%08x' % (d.group(1).strip(), (dep + off) & 0xffffffff)
                    new.append(x)
                    off += slot_bytes(t) if st == 'stack' else 0
                else:
                    out.append((j + 1, e, ','.join(new)))
        for s_, e_, t in sorted(out, reverse=True):
            code = code[:s_] + t + code[e_:]
        return code
    code = retaddr_at_call(code)
    # a value built in the outgoing arguments through a pointer to them ('push ecx; mov ecx, esp; push ecx; call
    # 0x4FCB40; call 0x511B30': 0x4FCB40 writes the argument of 0x511B30): the call that takes that slot must pass
    # the variable of the slot; the decompiler may pass a stale value instead (0x505330 handed 0x511B30 another
    # variable and the battle test crashed)
    bad = outgoing_mismatch(a, code)
    if bad:
        if not FORCE[0]:
            return None, bad
        NOTES.append(bad)
    for v in set(re.findall(r'(?m)^[ \t]*\w[\w ]*?[\s*]+(in_stack_ff[0-9a-f]{6})\s*(?:\[\d+\])?;$', code)):
        if len(re.findall(r'\b%s\b' % v, code)) == 1:
            code = re.sub(r'(?m)^[ \t]*\w[\w ]*?[\s*]+%s\s*(?:\[\d+\])?;\n' % v, '', code)
    # the return addresses then left in variables go where every read of the variable follows another store to
    # it in its own block (0x5A9550's 'uVar18 = 0x5a95a9', the variable used again for other values)
    def dead_store(v, at):
        lines = code.split('\n')
        # (the indentation of a statement's first line for the lines it continues on)
        indent, prev = [], None
        for l in lines:
            own = len(l) - len(l.lstrip())
            cont = prev is not None and prev.strip() and not re.search(r'[;{}:]\s*$', prev)
            indent.append(indent[-1] if cont and indent else own)
            if l.strip():
                prev = l
        for j, l in enumerate(lines):
            # (a store that reads the variable too, 'uVar2 = f(x, uVar2);' at 0x48FB40, is a read)
            if j == at or not re.search(r'\b%s\b' % v, l) or \
                    (re.match(r'\s*%s = [^=]' % v, l) and not re.search(r'\b%s\b' % v, l.split('=', 1)[1])) or \
                    re.match(r'\s*[A-Za-z_][\w ]*?\**\s*\b%s\s*;\s*$' % v, l):
                continue
            ind = indent[j]
            k = j
            while k > 0:
                k -= 1
                lk = lines[k]
                if not lk.strip():
                    continue
                # an if/else chain ending here, every branch storing to the variable, is a store
                if lk.strip() == '}' and indent[k] == ind:
                    def stmt_start(q):
                        while q > 0 and lines[q - 1].strip() and not re.search(r'[;{}:]\s*$', lines[q - 1]):
                            q -= 1
                        return q
                    parts, end_, final_else, ok = [], k, None, False
                    while True:
                        o = next((q for q in range(end_ - 1, -1, -1) if indent[q] == ind and lines[q].strip()), None)
                        if o is None or not lines[o].rstrip().endswith('{'):
                            break
                        head = lines[stmt_start(o)].strip()
                        parts.append((o, end_))
                        if final_else is None:
                            final_else = head in ('else {', '} else {')
                        if re.match(r'if\s*\(', head):
                            ok = True
                            break
                        if head.startswith('} else'):
                            end_ = o
                        elif head.startswith('else'):
                            p_ = next((q for q in range(stmt_start(o) - 1, -1, -1) if lines[q].strip()), None)
                            if p_ is None or lines[p_].strip() != '}' or indent[p_] != ind:
                                break
                            end_ = p_
                        else:
                            break
                    def stores(o_, e_):
                        body = [r for r in range(o_ + 1, e_) if lines[r].strip()]
                        return body and any(re.match(r'\s*%s = [^=]' % v, lines[q]) and
                                            indent[q] == min(indent[r] for r in body) for q in body)
                    if ok and final_else and all(stores(o_, e_) for o_, e_ in parts):
                        break
                    continue
                if indent[k] < ind or k == at:
                    if os.environ.get('AD_DEBUG'):
                        print('dead_store', v, 'read', j, repr(l), 'stopped at', k, repr(lk))
                        for q in range(k, j + 1):
                            if indent[q] <= ind and lines[q].strip():
                                print('   ', q, indent[q], repr(lines[q][:100]))
                    return False
                if indent[k] == ind and re.match(r'\s*%s = [^=]' % v, lk) and \
                        not re.search(r'\b%s\b' % v, lk.split('=', 1)[1]):
                    break
            else:
                return False
            if k == 0:
                return False
        return True
    for m in list(re.finditer(r'(?m)^[ \t]*(\w+) = 0x([0-9a-f]{6,8});\n', code)):
        if int(m.group(2), 16) in rets_here and \
                dead_store(m.group(1), code[:m.start()].count('\n')):
            code = code.replace(m.group(0), '', 1)
    if any(int(x, 16) in rets_here for x in re.findall(r'\b0x([0-9a-f]{6,8})\b', code)):
        if not FORCE[0]:
            return None, 'return address as a value (stack depth lost)'
        NOTES.append('return address as a value (stack depth lost)')
    # comments before the definition (the demangled name of an exported function, its own signature with '(void)'
    # that the parameter parsing would take for the definition's), once the warnings among them have been seen
    code = re.sub(r'^(?:\s*/\*.*?\*/)+', '', code, flags=re.S)
    # a callee that reads EBP as the frame of its caller (a funclet: 0x5E4197, the CRT's eh vector constructor
    # iterator, calls 0x5E41E4, which tests [ebp-20h]): no C function keeps the original frame in EBP
    for c in f['callees']:
        if 'EBP' in ebp_in.get(int(c, 16), ()):
            if not FORCE[0]:
                return None, 'callee %s reads the caller\'s EBP' % c
            NOTES.append('callee %s reads the caller\'s EBP' % c)
    code0 = code
    code, why = rewrite_icalls(code, f.get('icallfloat'))
    if code is None:
        if not FORCE[0]:
            return None, why
        NOTES.append(why + ' (left as the decompiler wrote it: (ICALL_<site>*<callee>)(...))')
        code = code0
    if has_indirect_call(code):
        return None, 'indirect call'
    pr = protos.get(a)
    if not pr:
        return None, 'no prototype'
    why = fit_convention(a, pr)
    if why:
        if not FORCE[0]:
            return None, why
        NOTES.append(why)
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
    # a class passed by value that is no 4-byte slot: the decompiler's guess for a dword it reads a byte of
    # (0x584190 GUIScene::vf15 'GUIScene param_3'); in C the callee would pop the whole class and wreck the
    # stack of its callers
    for t, _n in plist:
        t = t.strip()
        if '*' not in t and STRUCT_SIZE.get(t, 0) > 4 and t not in BYVALUE:
            return None, 'class %s passed by value (%d bytes)' % (t, STRUCT_SIZE[t])
    if ret.startswith('undefined') and not re.search(r'\breturn\s+[^;\s]', re.sub(r'/\*.*?\*/', '', body, flags=re.S)):
        ret = 'void'               # the decompiler guessed a result that the function never sets
    # (a function that only throws never returns: what its callers do with EAX after it is never run, 0x4488D0)
    if ret == 'void' and a in eax_used and a not in never_returns:
        if not FORCE[0]:
            return None, 'callers use EAX, the decompiler found no result'
        NOTES.append('callers use EAX, the decompiler found no result')
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
        # (also through a cast: 'ppuStack_8 = (undefined1 **)&((void *)G_005E6394);', 0x432700)
        hs = re.findall(r'\b((?:pu|pc|p)\w*Stack_\w+)\s*=\s*(?:\([\w ]+(?:\s*\*)+\)\s*)?&?\s*'
                        r'(?:&?(?:LAB|FUN)_|\(\([\w ]+(?:\s*\*)+\)G_)([0-9a-fA-F]{8})\b', body)
        # (other pointers to code or data stored in the frame, 0x50C3C0: the handler's slot is the one under the
        # state, at -8, or -0xc after an aligned frame)
        if len(set(hs)) > 1:
            hs = [h for h in hs if re.search(r'Stack_(?:8|c)$', h[0])] or hs
        hs = sorted(set(h[1] for h in hs))
        # (the prologue's own push of the handler, where the text shows several pointers or none: 0x49FE20 keeps it
        # at -0x10 after an aligned frame, 0x4B4700 shows no variable for it)
        if len(hs) != 1 and prologue_handler(a) is not None:
            hs = ['%08X' % prologue_handler(a)]
        if len(hs) != 1:
            if os.environ.get('AD_DEBUG'):
                print('handler %08X' % a, hs, re.findall(r'.*Stack_\w+\s*=\s*[^;]*G_[0-9A-F]{8}.*', body)[:4])
            if not FORCE[0]:
                return None, 'exception frame without a known handler'
            NOTES.append('exception frame without a known handler')
        if hs and catches(int(hs[0], 16)):
            if not FORCE[0]:
                return None, 'catches exceptions'
            NOTES.append('catches exceptions')
    # the statements on the SEH chain go; a variable given its head and used elsewhere would be left unset (0x491F50
    # passes 'in_eax = ExceptionList' on to 0x491CF0 when a branch does not set it): it reads fs:[0] itself
    # the head of the chain: the global at fs:[0] (G_FFDFF000), the TEB's ExceptionList, or what unaff_FS_OFFSET
    # points at (*unaff_FS_OFFSET: 0x421020)
    fshead = r'(?:\bG_FFDFF000\b|\bExceptionList\b|\*\s*unaff_FS_OFFSET\b)'
    body = re.sub(r'(?m)^[ \t]*[A-Za-z_][\w ]*?[\s*]+(?:unaff_FS_OFFSET|ExceptionList)\s*;[ \t]*\n', '', body)
    for v in set(re.findall(r'(?m)^\s*(\w+)\s*=\s*(?:\([^()]*\)\s*)?%s\s*;' % fshead, body)):
        if any(re.search(r'\b%s\b' % v, st) and not re.search(fshead, st) and not re.match(r'\s*#define', st) and
               not re.match(r'\s*[A-Za-z_][\w ]*?[\s*]+%s\s*(?:\[\d+\])?\s*;\s*$' % v, st)
               for st in re.findall(r'[^;{}]*[;{}]', body)):
            body = re.sub(r'(?m)^(\s*%s\s*=\s*(?:\([^()]*\)\s*)?)%s(\s*;)' % (v, fshead), r'\1GH_FS0\2', body)
    # then the chain's own statements go: its writes (also inside expressions, '(G_FFDFF000 = &local_c, cond)':
    # 0x47DEB0) and the saves of the fshead in variables used nowhere else; whatever else reads it reads fs:[0]
    # itself (the upper bytes of a bool result left from loading it: 0x438D70)
    body = re.sub(r'%s\s*=\s*&?\s*\w+\s*,\s*' % fshead, '', body)
    body = re.sub(r'(?m)^[ \t]*%s\s*=\s*[^;\n]*;[ \t]*\n' % fshead, '', body)
    body = re.sub(r'(?m)^[ \t]*\w+\s*=\s*(?:\([^()]*\)\s*)?%s\s*;[ \t]*\n' % fshead, '', body)
    body = re.sub(r'%s(?!\s*=[^=])' % fshead, 'GH_FS0', body)

    # vftable of the function's own class
    own = symname.get(a, '')
    if '::' in own:
        cls = own.rsplit('::', 1)[0]
        # (not a field 'x.vftable' or 'p->vftable', which the decompiler may break across lines)
        body = re.sub(r'(?<![\w:.>])(vftable(?:_\w+)?)\b',
                      lambda m: m.group(1) if re.search(r'(?:\.|->)\s*$', body[max(0, m.start() - 40):m.start()])
                      else cls + '::' + m.group(1), body)
    # the x87 control word as fnstcw stored it (the decompiler's in_FPUControlWord, never set: 0x58B200 returned it
    # with the truncation bits for its caller's fldcw, garbage in C)
    body = re.sub(r'(?m)^\s*\w+\s+in_FPUControlWord;\n', '', body)
    body = re.sub(r'\bin_FPUControlWord\b', 'GH_FNSTCW', body)
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
            if m.group(1) == '_decomp_StrByValue':
                continue                       # a whole string taken from there (the rules above)
            if re.search(r'\b(?:%s)\s+in_stack_%08x\s*;' % ('|'.join(BYVALUE), off), flat):
                continue                       # one variable of the whole object, passed by value (0x42AF50)
            need = OBJ_DWORDS.get(m.group(1))
            if need is None:
                need = outgoing_object_dwords(a, off)
            run = 0
            for r in re.finditer(r'\bin_stack_%08x\b(?:\s*,\s*(?:in_stack_|\*\(\w+ \*+\)&stack0x)ff[0-9a-f]{6}\b)*'
                                 % off, flat):
                n = 0
                for v in re.findall(r'(?:in_stack_|&stack0x)(ff[0-9a-f]{6})', r.group(0)):
                    if int(v, 16) != off + 4 * n:
                        break
                    n += 1
                run = max(run, n)
            if need is None or run < need:
                if os.environ.get('AD_DEBUG'):
                    print('outgoing %08X off %x type %s need %s run %d:' % (a, off, m.group(1), need, run),
                          sorted(set(x for x in re.findall(r'[^;{}]*\bin_stack_%08x\b[^;{}]*' % off, flat)))[:3])
                if not FORCE[0]:
                    return None, 'object built in the outgoing arguments, passed on in part'
                NOTES.append('object built in the outgoing arguments, passed on in part')
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
    # (so is an EAX the decompiler declared but never set, what a callee left: 0x547F10 hands 0x4AC7F0, which
    # passes EAX through, the EAX of 0x473110's float result)
    for v in re.findall(r'(?m)^\s*(?:undefined4|u?int|uint|[\w ]+\*+)\s*(in_eax(?:_\d+)?);$', body):
        if not re.search(r'\b%s\s*=[^=]' % v, body):
            body = re.sub(r'(?m)^(\s*(?:undefined4|u?int|uint|[\w ]+\*+)\s*%s);$' % v, r'\1 = 0;', body)
    # stack variables at their original offsets: the decompiler splits buffers and structures into scalars that the
    # original kept side by side (and walks across them with pointers), so all named stack variables become views
    # of one frame array laid out as the original stack frame (local_1c is at -0x1c from the return address)
    body, frame_names = stack_frame(body)
    if body is None:
        if not FORCE[0]:
            return None, frame_names
        NOTES.append(frame_names)
    # labels keep their names (the address substitution below is for LAB_ used as a value)
    body = re.sub(r'\bgoto\s+(LAB_[0-9a-fA-F]{8})\b', r'goto L\1', body)
    body = re.sub(r'^(\s*)(LAB_[0-9a-fA-F]{8}):', r'\1L\2:', body, flags=re.M)
    # '(undefined4)x' of a float variable is the decompiler's cast of the bits (an fstp to a dword: 0x587D30 stores
    # a float read from Lua into an array this way); in C it would convert the value (text placed off screen)
    fl = {}
    for t_, n_ in re.findall(r'(?m)^\s+(float10|double|float)\s+(\w+)\s*;', body):
        fl[n_] = t_
    for t_, n_ in [(x.rsplit(' ', 1) + [''])[:2] for x in params]:
        if t_.strip() in ('float', 'double', 'float10'):
            fl[n_] = t_.strip()
    def bits(m):
        n_, v = int(m.group(1)), m.group(2)
        if v not in fl:
            return m.group(0)
        if n_ == 4:
            return 'BITCAST(undefined4, ((float)(%s)))' % v
        if n_ == 8:
            return 'BITCAST(undefined8, ((double)(%s)))' % v
        bad_cast.append(v)
        return m.group(0)
    bad_cast = []
    body = re.sub(r'\(undefined([1248])\)\s*(\w+)\b(?!\s*[\[(.])', bits, body)
    if bad_cast:
        if not FORCE[0]:
            return None, 'float variable cast to a smaller undefined type'
        NOTES.append('float variable cast to a smaller undefined type')
    # pieces of a variable: v._1_3_ is the 3 bytes at offset 1 of v; a 3-byte store is a 2-byte and a 1-byte one
    body = re.sub(r'(?m)^(\s*)([A-Za-z_]\w*)\._(\d+)_3_ = ([^;\n]+);$',
                  lambda m: '%s{ unsigned int gh3 = (unsigned int)(%s); *(unsigned short *)((char *)&%s + %d) = '
                            '(unsigned short)gh3; *(unsigned char *)((char *)&%s + %d) = (unsigned char)(gh3 >> 16); }'
                            % (m.group(1), m.group(4), m.group(2), int(m.group(3)), m.group(2), int(m.group(3)) + 2), body)
    bad = []
    def piece(m):
        var, off, size = m.group(1), int(m.group(2)), int(m.group(3))
        if size not in (1, 2, 3, 4, 8):
            bad.append(m.group(0))
        if size == 3 and re.match(r'\s*=[^=]', body[m.end():m.end() + 3]):
            bad.append(m.group(0))   # a 3-byte store has no C type
        t = {1: 'unsigned char', 2: 'unsigned short', 3: 'unsigned int', 4: 'unsigned int', 8: 'unsigned long long'}.get(size, 'int')
        return '(*(%s *)((char *)&%s + %d))' % (t, var, off)
    # (of a field or an element too: 'aCStack_124[0].field2_0x8._16_1_', 0x57C8D0)
    body = re.sub(r'\b([A-Za-z_]\w*(?:\[[^\[\]]*\]|(?:\.|->)(?!_\d+_\d+_)[A-Za-z_]\w*)*)\._(\d+)_(\d+)_\b',
                  piece, body)
    # a piece holding a pointer, dereferenced ('*(undefined1 **)*dStack_47c._0_4_', 0x574830): through an
    # unsigned int * (the piece is an unsigned int in C)
    body = re.sub(r'((?:\(\s*[A-Za-z_][\w ]*\*+\s*\)|[=(,]|^)\s*)\*(\(\*\(unsigned int \*\)\(\(char \*\)&)',
                  r'\1*(unsigned int *)\2', body, flags=re.M)
    if bad:
        if not FORCE[0]:
            return None, 'piece of a variable'
        NOTES.append('piece of a variable')
    # a value stored to a piece keeps its bits when it is a float ('v._4_4_ = fVar2 + fVar2' in 0x572170; 0x587D30
    # 'v._0_4_ = *(float *)(this + 0x5c) + ...' placed the character window's text off screen): the compiler, which
    # knows the type of the expression, picks (ghidra_prelude.h GH_BITS4/GH_BITS8)
    body = re.sub(r'(\(\*\((unsigned int|unsigned long long) \*\)\(\(char \*\)&\w+ \+ \d+\)\)) = ([^;]+);',
                  lambda m: '%s = %s(%s);' % (m.group(1), 'GH_BITS4' if m.group(2) == 'unsigned int' else 'GH_BITS8',
                                              m.group(3)), body)
    # void * dereferenced: the decompiler did not know the type of the value (int or float), neither do we
    for t_, n_ in [(x.rsplit(' ', 1) + [''])[:2] for x in params]:
        n_ = n_.lstrip('*')
        if t_.strip() == 'void' and re.search(r'(?<![\w)])\*%s\b' % re.escape(n_), body):
            if not FORCE[0]:
                return None, 'void pointer dereferenced'
            NOTES.append('void pointer dereferenced')
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
    # (a table of string pointers: '(&PTR_s_giant.tga_006c3dc0)[iVar2]', 0x53B2E0)
    body = re.sub(r'\(&PTR_s_[\w.]*?_([0-9a-fA-F]{8})\)\[', lambda m: '((char **)d_%s)[' % m.group(1).upper(), body)
    # (names of strings keep their dots: 's_luac.out_006c1fac', 0x4B42C0)
    body = re.sub(r'&?\b(LAB|PTR_LAB|PTR_FUN|PTR_DAT|PTR_s|FUN|s_[\w.]+?|u_[\w.]+?)_([0-9a-fA-F]{8})\b', addr_ref, body)
    # the address of untyped data is just an address
    body = re.sub(r'&(?:DAT|UNK)_([0-9a-fA-F]{8})\b(?!\s*[\[.])', lambda m: '((void *)d_%s)' % m.group(1).upper(), body)
    for x in re.findall(r'\(\((?:void \*|char \*\*)\)d_([0-9A-F]{8})\)', body):
        extra.add(x)
    if re.search(r'(?<![\w.>])(DAT_|PTR_|BYTE_|WORD_|DWORD_|UNK_)[0-9a-fA-F]{8}\b', body):
        if not FORCE[0]:
            return None, 'global of unknown type'
        NOTES.append('global of unknown type')
    try:
        body = re.sub(r'&?(?:\b[A-Za-z_][\w<>,]*(?:<[^;{}()]*?>)?::)+(?:vftable(?:_\w+)?|vbtable\w*|`[^`]*\'|\w+_meta_ptr)', sym_ref, body)
    except KeyError as e:
        return None, 'unknown symbol %s' % e
    # a small constant the decompiler took for an address ('&((void *)G_00000004)' passed on: 0x431100)
    body = re.sub(r'&?\s*\(\((\w+(?:\s*\*)+)\)\s*G_(0000[0-9A-F]{4})\)', lambda m: '((%s)0x%X)' % (m.group(1), int(m.group(2), 16)), body)
    for g in re.findall(r'\bG_([0-9A-F]{8})\b', body):
        ad = int(g, 16)
        if not (0x401000 <= ad < 0x1000000):        # (the headers at 400000 are no section)
            if not FORCE[0]:
                return None, 'segment or out-of-image global'
            NOTES.append('segment or out-of-image global')
    for x in re.findall(r'\(\(void \*\)d_([0-9A-F]{8})\)', body):
        extra.add(x)
    if '::' in body:
        if not FORCE[0]:
            return None, 'C++ name left'
        NOTES.append('C++ name left')
    if any(not (0x401000 <= int(x, 16) < 0x1000000) for x in extra):
        if not FORCE[0]:
            return None, 'address outside the image'
        NOTES.append('address outside the image')

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
            if not FORCE[0]:
                return None, 'callee %s without prototype' % c
            NOTES.append('callee %s without prototype' % c)
        if ca in imports:
            if ca not in impnames:
                if not FORCE[0]:
                    return None, 'import %s not in the import table' % c
                NOTES.append('import %s not in the import table' % c)
            icc, _, iret, iplist, iva = cp[:5]
            # a C function of varargs (sprintf) whose variable arguments the decompiler lost: 0x5111E0 called
            # 'sprintf(buf, "%s 1. %s")' with the two strings gone and the game faulted.  Each call in the text
            # must have an argument count the machine code's calls clean up after them ('add esp, N')
            if iva and icc == '__cdecl':
                seen = vararg_counts(a, ca)
                for cm in re.finditer(r'\bsub_%s\s*\(' % c, code):
                    depth, q = 1, cm.end()
                    while q < len(code) and depth:
                        depth += {'(': 1, ')': -1}.get(code[q], 0)
                        q += 1
                    # (in dwords: a double or long long passed counts two, ghidra/VarargsCalls.java types them from
                    # the format)
                    wide = set(re.findall(r'(?m)^\s*(?:double|longlong|ulonglong|undefined8)\s+(\w+)\s*;', code))
                    n = sum(2 if re.match(r'\(\s*(?:double|longlong|ulonglong)\s*\)', x) or x in wide or
                            re.fullmatch(r'GV_\w+_8', x) else 1 for x in split_args(code[cm.end():q - 1]))
                    if seen and n not in seen:
                        if not FORCE[0]:
                            return None, 'varargs call of %s with %d arguments, the machine code passes %s' % (
                                c, n, ','.join(map(str, sorted(seen))))
                        NOTES.append('varargs call of %s with %d arguments' % (c, n))
            if not iva and ca in import_args:
                ps_ = iplist[1:] if icc == '__thiscall' else iplist[2:] if icc == '__fastcall' else iplist
                have = sum(slot_bytes(t) for t, _ in ps_)
                cleaned, pushed = import_args[ca]
                need = 4 * pushed if icc in ('__stdcall', '__thiscall', '__fastcall') else cleaned
                # (the pushes before a call that pops its own arguments may be the next call's, pushed early: the
                # prototypes of the system DLLs and of the C++ runtime, from Ghidra's type libraries and the
                # decorated names, are trusted for those; GetStdHandle had 3 pushes before it)
                dll = image[0].imports.get(ca, ('', ''))[0].upper()
                if need != cleaned and dll in SYSTEM_DLLS:
                    need = 0
                if need > have:
                    if not FORCE[0]:
                        return None, 'import %s takes more arguments than its prototype' % c
                    NOTES.append('import %s takes more arguments than its prototype' % c)
            w = cc_word(icc, False) or '__cdecl'
            # (a class passed by value to the C++ runtime is a one-dword wrapper, std::string's _Size_type_nosscl
            # around an index (operator[], 0x46D380): the call passes the number, an unsigned int in C)
            ps = ', '.join('unsigned int' if t.startswith('_Demangler_') and '*' not in t else t
                           for t, n in iplist) if iplist else 'void'
            if iva:
                ps += ', ...'
            decls.append('DECOMP_C %s (%s *imp_%s)(%s) __asm__("%s");' % (wide_ret(iret), w, c, ps, impnames[ca]))
            decls.append('#define sub_%s (*imp_%s)' % (c, c))
            continue
        why = fit_convention(ca, cp)
        if why:
            if not FORCE[0]:
                return None, 'callee %s: %s' % (c, why)
            NOTES.append('callee %s: %s' % (c, why))
        t = proto_text('sub_%s' % c, cp)
        if t is None:
            if not FORCE[0]:
                return None, 'callee %s with unknown calling convention' % c
            NOTES.append('callee %s with unknown calling convention' % c)
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
            # (subscripted: a byte one the bytes from there, 'G_006C0BE4[0x1f]' 'cmp byte ptr [0x6c0c03], bl' in
            # 0x464690; not a dword one, a pointer of elements of a type the decompiler does not say,
            # 'G_006CA2C4[0x13]' floats in 0x449440)
            if parts[0] in ('undefined1', 'char', 'byte', 'uchar', 'bool'):
                body = re.sub(r'\bG_%s\[' % g, '((%s *)d_%s)[' % (parts[0], g), body)
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
                    help='addresses left out (e.g. 401000-4205A0, the Lua 5.1 library: build it from its sources)')
    ap.add_argument('--icalls', help='call-site prototypes of indirect calls (ghidra/ICallOverride.java output)')
    ap.add_argument('--functions', required=True, help='symbols/<game>_functions.tsv (machine-code register inputs)')
    ap.add_argument('--draft', metavar='ADDR,...', help='only write drafts for hand work of these functions into '
                    '--draft-dir (DIR/f_ADDR.c: the text made also where the function is rejected, the reasons on '
                    'top), nothing else')
    ap.add_argument('--draft-dir', default='drafts')
    a = ap.parse_args()
    load_machine(a.functions)
    if a.icalls:
        for l in open(a.icalls):
            q = l.rstrip('\n').split('\t')
            if l[0] != '#' and len(q) == 4:
                icalls[int(q[0], 16)] = (q[1], int(q[2]), q[3])
        # (the machine-code facts next to it, tools/icalls.py: pops of indirect calls the decompiler made no
        # CALLIND of, so no override: 'call ebp' of an import kept in EBP, 0x5302E0)
        facts = os.path.join(os.path.dirname(a.icalls), os.path.basename(a.icalls).replace('_icall_overrides', '_icalls'))
        if facts != a.icalls and os.path.exists(facts):
            for l in open(facts):
                q = l.rstrip('\n').split('\t')
                if l[0] != '#' and len(q) == 6:
                    icall_pops[int(q[0], 16)] = 0 if int(q[3]) >= 0 else int(q[5]) if int(q[5]) >= 0 else None
    ex = a.functions.replace('_functions.tsv', '_eaxin.tsv')
    if os.path.exists(ex):
        eax_handers.update(int(l.split()[0], 16) for l in open(ex) if l.strip() and l[0] != '#')
    rl = a.functions.replace('_functions.tsv', '_retlive.tsv')
    if os.path.exists(rl):
        eax_used.update(int(l, 16) for l in open(rl) if l.strip() and l[0] != '#')
    os.makedirs(a.outdir, exist_ok=True)
    protos, imports = load_protos(a.jsonl + '.protos')
    for ia in imports:
        icc, _, _, iplist, iva = protos[ia][:5]
        skip_ = 1 if icc == '__thiscall' else 2 if icc == '__fastcall' else 0
        import_pops[ia] = 0 if iva or icc not in ('__stdcall', '__thiscall', '__fastcall') else \
            sum(slot_bytes(t) for t, _ in iplist[skip_:])
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
    for fa, (_, pop) in machine.items():
        if not fsize.get(fa):
            continue
        try:
            ins = list(md.disasm(pe.read(fa, fsize[fa]), fa))
        except Exception:
            continue
        if ins and sum(i.size for i in ins) == fsize[fa] and not any(
                i.mnemonic.startswith('ret') or (i.mnemonic == 'jmp' and not (
                    i.operands[0].type == cx.X86_OP_IMM and fa <= i.operands[0].imm < fa + fsize[fa])) for i in ins):
            never_returns.add(fa)
            if pop is None:
                noreturn.add(fa)
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
    ONE_BYTE.update(re.findall(r'_Static_assert\(sizeof\((_Demangler_\w+)\) == 1,', types))
    STRUCT_SIZE.update((t, int(n)) for t, n in re.findall(r'_Static_assert\(sizeof\((\w+)\) == (\d+),', types))
    # structures the types header cut short (their last bytes one pad array): where the pad starts
    TRUNCATED.update(('_' + t, int(n, 16) + 1) for t, n in re.findall(
        r'\nstruct _(\w+) \{(?:(?!\n\};)[\s\S])*?\n    unsigned char field_0x([0-9a-f]+);\n    unsigned char pad_\d+\[\d+\];\n\};', types))
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
    # a variable read before anything set it is a value the decompiler lost (0x520380 passes three unset 'this'
    # pointers on): the original read whatever a register held, C reads garbage of its own
    cflags = [x for x in cflags if x != '-w'] + ['-Wno-everything', '-Werror=uninitialized',
                                                 '-Werror=sometimes-uninitialized', '-Werror=conditional-uninitialized']
    pch = pre + '.pch'
    r = subprocess.run(['clang'] + cflags[:1] + ['-x', 'c-header', '-std=gnu11', '-fms-extensions', '-ffreestanding',
                        '-w'] + inc + [pre, '-o', pch], capture_output=True, text=True)
    if r.returncode:
        sys.stderr.write(r.stderr[:4000]); sys.exit('the types header does not compile')
    funcs = [json.loads(l) for l in open(a.jsonl, encoding='utf-8')]
    for f in funcs:
        c = f['code']; i = c.find('{'); h = c[:i]
        if i < 0 or ')' not in h:
            continue
        ps = h[h.rfind('(', 0, h.rfind(')')) + 1:h.rfind(')')]
        if h.rfind(')') < 0 or re.search(r'\(\s*\*', h[h.rfind('(', 0, h.rfind(')')) - 2:]):
            continue
        ps = split_args(ps)
        names = [re.findall(r'(\w+)(?:\s*\[\d*\])?\s*$', p) for p in ps]
        unused_params[int(f['a'], 16)] = {n for n, m in enumerate(names)
                                          if m and m[0] != 'void' and not re.search(r'\b%s\b' % m[0], c[i:])}
    if a.max:
        funcs = funcs[:a.max]
    status = {}
    cands = []
    ranges = [tuple(int(x, 16) for x in r.split('-')) for r in a.exclude_range]
    if a.draft:
        want = {int(x, 16) for x in a.draft.split(',')}
        os.makedirs(a.draft_dir, exist_ok=True)
        FORCE[0] = True
        for f in funcs:
            if int(f['a'], 16) not in want:
                continue
            NOTES.clear()
            res, why = convert(f, protos, skip, imports, impnames)
            out = os.path.join(a.draft_dir, 'f_%s.c' % f['a'])
            if res is None:
                print('%s: no draft: %s' % (f['a'], why))
                continue
            addr, decls, text = res
            with open(out, 'w', encoding='utf-8') as o:
                o.write('/* draft of 0x%08X for hand work (tools/autodecomp.py --draft); the generated code was '
                        'rejected:\n' % addr + ''.join(' *   %s\n' % n for n in NOTES) + ' */\n')
                o.write('#include "auto_pre.h"\n')
                if addr in convs:   # (rebuild/build.py: the registers in parameter order and the pop)
                    o.write('/* @conv %s %d */\n' % (','.join(convs[addr][0]) or '-', convs[addr][1]))
                o.write('\n'.join(decls) + '\n' + text)
            print('%s: %s (%d notes)' % (f['a'], out, len(NOTES)))
        return
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
