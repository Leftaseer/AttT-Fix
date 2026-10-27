#!/usr/bin/env python3
"""Stack parameters each function really uses, from the machine code: follows ESP through the function
(push/pop, sub/add esp, calls with the ret pop of the callee from functions.tsv) and EBP frames, and records the
highest stack slot above the return address that is read, written or addressed.  The decompiler misses
parameters a function only passes on to a call (Lua's lua_pushlstring takes (L, s, len) and hands s and len to
luaS_newlstr untouched), and every caller is then decompiled without those arguments.

usage: stackparams.py EXE symbols/GAME_functions.tsv OUT.tsv [AUTO.jsonl.protos (conventions of imports)]
                      [ICALLS.tsv (tools/icalls.py: bytes indirect callees pop)]
OUT: address, number of 4-byte stack slots used (0 if none), 'exact' or 'lost' (ESP could not be followed
everywhere, e.g. after an indirect call with unknown cleanup: the count is a lower bound), and the slots (0 = the
first parameter) read as whole dwords and never written: such a parameter is 4 bytes even where the decompiler
typed it as a byte (0x42AF50 passes its second parameter on as a pointer, typed undefined1 its callers cut the
pointer down to a byte); the arguments callers push; and the slots only x87/SSE float instructions use, as
'k:f' (a float) or 'k:d' (a double in slots k and k+1): sqrt(x) of 0x406260 has x untyped, and its callers
then pass the bits of a float as an integer."""
import sys, re, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import PE
import capstone
from capstone import x86
from stackfx import table_import_pops, cleanup_after, switch_targets, prologue_end

pe = PE(sys.argv[1])
funcs = {}
for l in open(sys.argv[2]):
    if l[0] == '#':
        continue
    q = l.rstrip('\n').split('\t')
    funcs[int(q[0], 16)] = (int(q[1]), 0 if q[3] == '?' else int(q[3] or 0))
imports = {}           # IAT slot -> bytes the imported function pops (from AutoExport's .protos, optional)
if len(sys.argv) > 4 and sys.argv[4] != '-':
    W8 = {'double', 'longlong', 'ulonglong', 'undefined8', 'qword'}
    for l in open(sys.argv[4], encoding='utf-8'):
        q = l.rstrip('\n').split('\t')
        if len(q) > 6 and q[6] == 'import':
            ps = [x.strip().rsplit(' ', 1)[0] for x in q[4].split(',') if x.strip()] if q[4] else []
            if q[1] == '__thiscall':
                ps = ps[1:]
            n = sum(8 if t in W8 else 4 for t in ps)
            imports[int(q[0], 16)] = n if q[1] in ('__stdcall', '__thiscall') and q[5] != 'true' else 0
icall_pop = {}         # indirect call -> bytes the callee pops (-1 unknown), from icalls.py
if len(sys.argv) > 5:
    for l in open(sys.argv[5]):
        q = l.rstrip('\n').split('\t')
        if l[0] != '#' and len(q) > 5:
            icall_pop[int(q[0], 16)] = int(q[5])
imports.update(table_import_pops(pe))
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
ESP, EBP = x86.X86_REG_ESP, x86.X86_REG_EBP


def frame_helper(a, size):
    """EBP after a call of a CRT frame helper (__SEH_prolog4, __EH_prolog: they push the SEH record and set up
    the caller's EBP frame), relative to ESP at the call; None for other functions.  _onexit (0x5E3ED2) reads its
    parameter as [ebp+8] after 'call __SEH_prolog4': without this it looked like it had none, and the generated
    atexit called it without the function to register (a crash at exit)."""
    try:
        ins = list(md.disasm(pe.read(a, min(size, 48)), a))
    except Exception:
        return None
    pushes = 0
    for k, i in enumerate(ins[:10]):
        o = i.operands
        if i.mnemonic == 'push':
            pushes += 1
        elif i.mnemonic == 'mov' and len(o) == 2 and o[0].type == x86.X86_OP_MEM and o[0].mem.base == ESP and \
                o[1].type == x86.X86_OP_REG and o[1].reg == EBP and k + 1 < len(ins):
            n = ins[k + 1]
            if n.mnemonic == 'lea' and n.operands[0].reg == EBP and n.operands[1].mem.base == ESP and \
                    n.operands[1].mem.disp == o[0].mem.disp:
                return -4 - 4 * pushes + o[0].mem.disp     # the return address, the pushes, then [esp+K]
            return None
        elif i.mnemonic in ('ret', 'call', 'jmp') or i.mnemonic.startswith('j'):
            return None
    return None


X87_CONTROL = ('fldcw', 'fnstcw', 'fstcw', 'fnstsw', 'fstsw', 'fnstenv', 'fstenv', 'fldenv', 'fnsave', 'fsave',
               'frstor', 'fbld', 'fbstp')
X87_STORES = ('fnstcw', 'fstcw', 'fnstsw', 'fstsw', 'fnstenv', 'fstenv', 'fnsave', 'fsave')


def float_width(i, op):
    """4 or 8 if the instruction reads or writes the memory operand as a float or double (x87 or SSE)"""
    m = i.mnemonic
    if m.startswith('f') and not m.startswith('fi') and m not in X87_CONTROL:
        return op.size if op.size in (4, 8) else None
    if m.startswith(('cvtsi2', 'cvtpi2')):
        return None
    if m.endswith(('ss', 'sd', 'ss2sd', 'sd2ss', 'ss2si', 'sd2si')) and m != 'movsd' or (m == 'movsd' and i.operands):
        return op.size if op.size in (4, 8) else None
    return None


def analyse(start, size):
    code = {}
    try:
        for i in md.disasm(pe.read(start, size), start):
            code[i.address] = i
    except Exception:
        return 0, 'lost', (), ()
    top = 0                    # highest byte offset above the return address seen (exclusive)
    dword_read, written = set(), set()
    floats, other = {}, set()  # slot -> widths of the float accesses to it; slots accessed otherwise
    lost = False
    todo = [(start, 0, None, frozenset())]  # address, esp delta (0 = at the return address), ebp delta or None,
                                            # parameter slots written on the way
    pushed = 0                 # bytes pushed since the last call: the arguments of the next one
    run = 0                    # pushes right before, with only moves between them
    # the prologue's pushes are saves (or the SEH frame), never arguments (0x479870)
    entry_end = prologue_end(code.get, start)
    seen = {}
    steps = 0
    while todo:
        p, d, bp, killed = todo.pop()
        while p in code and steps < 20000:
            if p in seen:
                break
            seen[p] = d
            steps += 1
            i = code[p]
            m = i.mnemonic
            for op in i.operands:
                if op.type == x86.X86_OP_MEM and op.mem.index == 0:
                    base = op.mem.base
                    off = None
                    if base == ESP and d is not None:
                        off = d + op.mem.disp
                    elif base == EBP and bp is not None:
                        off = bp + op.mem.disp
                    if off is not None and off >= 4:
                        top = max(top, off + (op.size if m != 'lea' else 4))
                        if m != 'lea' and (off - 4) % 4 == 0:
                            k = (off - 4) // 4
                            if op.access & capstone.CS_AC_WRITE:
                                written.add(k)
                            elif op.size == 4 and op.access & capstone.CS_AC_READ:
                                dword_read.add(k)
                        # what the parameter's value is used as: until a write on this path makes the slot a
                        # temporary of the function (MSVC reuses dead parameter slots)
                        cover = range((off - 4) // 4, (off - 4 + max(op.size, 1) + 3) // 4)
                        fw = float_width(i, op)
                        acc = capstone.CS_AC_WRITE if m in X87_STORES else op.access   # capstone has them read
                        if any(k in killed for k in cover):
                            pass
                        elif fw and (off - 4) % 4 == 0 and m != 'lea' and acc & capstone.CS_AC_READ:
                            k = (off - 4) // 4
                            floats.setdefault(k, set()).add(fw)
                            if fw == 8:
                                floats.setdefault(k + 1, set()).add(-8)
                        elif m == 'lea' or acc & capstone.CS_AC_READ:
                            other.update(cover)
                        if m != 'lea' and acc & capstone.CS_AC_WRITE:
                            killed = killed | set(cover)
            # ESP and EBP tracking
            ops = i.operands
            if m == 'push':
                d = None if d is None else d - 4
                pushed += 4
            elif m == 'pop':
                if ops and ops[0].type == x86.X86_OP_REG and ops[0].reg == EBP:
                    bp = None
                d = None if d is None else d + 4
            elif m == 'mov' and ops[0].type == x86.X86_OP_MEM and ops[0].mem.segment == x86.X86_REG_FS:
                pushed = 0             # SEH frame registered: the pushes so far were the prologue's
            elif m in ('sub', 'add') and ops[0].type == x86.X86_OP_REG and ops[0].reg == ESP:
                if m == 'sub':
                    pushed = 0         # frame allocation: the end of the prologue
                if ops[1].type == x86.X86_OP_IMM and d is not None:
                    d = d - ops[1].imm if m == 'sub' else d + ops[1].imm
                else:
                    d = None
            elif m == 'mov' and ops[0].type == x86.X86_OP_REG and ops[0].reg == EBP:
                bp = d if (ops[1].type == x86.X86_OP_REG and ops[1].reg == ESP) else None
            elif m == 'mov' and ops[0].type == x86.X86_OP_REG and ops[0].reg == ESP:
                d = bp if (ops[1].type == x86.X86_OP_REG and ops[1].reg == EBP) else None
            elif m == 'lea' and ops[0].type == x86.X86_OP_REG and ops[0].reg == ESP:
                mem = ops[1].mem
                d = (bp + mem.disp) if (mem.base == EBP and bp is not None and mem.index == 0) else \
                    (d + mem.disp) if (mem.base == ESP and d is not None and mem.index == 0) else None
            elif m == 'and' and ops[0].type == x86.X86_OP_REG and ops[0].reg == ESP:
                d = None               # aligned frame: only EBP-relative accesses count from here
            elif m == 'leave':
                d = None if bp is None else bp + 4
                bp = None
            elif m == 'call' and ops[0].type == x86.X86_OP_IMM and ops[0].imm in helpers:
                bp = None if d is None else d + helpers[ops[0].imm]
                d = None               # the helper allocated the frame: EBP-relative accesses from here
                pushed = 0
            elif m == 'call':
                if ops[0].type == x86.X86_OP_IMM and ops[0].imm in funcs:
                    if d is not None:
                        d += funcs[ops[0].imm][1]
                elif ops[0].type == x86.X86_OP_MEM and ops[0].mem.base == 0 and ops[0].mem.index == 0 and \
                        ops[0].mem.disp in imports:
                    if d is not None:
                        d += imports[ops[0].mem.disp]
                else:
                    # unknown callee (import, pointer, helper): cdecl if the caller cleans up right after,
                    # otherwise the callee popped what the ESP balance says (icalls.py), else the pushes right
                    # before the call (not the prologue's pushes of saved registers: 0x42A720's 'push 1; call edx'
                    # after 'push ecx; push esi' made a local look like a parameter)
                    caller_cleans = cleanup_after(code.get, i.address + i.size) >= 0
                    if d is not None and not caller_cleans:
                        d += icall_pop[i.address] if icall_pop.get(i.address, -1) >= 0 else 4 * run
                pushed = 0
            # pushes right before the next instruction, with only moves between them
            run = run + (i.address >= entry_end) if m == 'push' else run if (m.startswith('mov') or m == 'lea' or m.startswith('fld') or
                                                       m.startswith('fst')) else 0
            if d is None and bp is None:
                lost = True
                break
            if m.startswith('ret'):
                break
            if m == 'jmp':
                if ops[0].type == x86.X86_OP_IMM and ops[0].imm in code:
                    p = ops[0].imm
                    continue
                if ops[0].type == x86.X86_OP_IMM and ops[0].imm in funcs and d == 0:
                    tails.setdefault(start, set()).add(ops[0].imm)
                for t in switch_targets(i, pe.u32, start, start + size):
                    todo.append((t, d, bp, killed))      # the cases of a switch
                break                  # tail jump, or the cases queued
            if m.startswith('j') or m.startswith('loop'):
                if ops[0].type == x86.X86_OP_IMM:
                    todo.append((ops[0].imm, d, bp, killed))
            p = i.address + i.size
    slots = max(0, (top - 4 + 3) // 4)
    fl = []
    for k in sorted(floats):
        w = floats[k]
        if k in other or len(w) != 1 or -8 in w:
            continue
        if w == {8} and (k + 1 in other or floats.get(k + 1) != {-8}):
            continue
        fl.append('%d:%s' % (k, 'f' if w == {4} else 'd'))
    return slots, 'lost' if lost else 'exact', sorted(dword_read - written), fl


tails = {}             # function -> functions it tail-jumps to with ESP at its return address (its parameters
                       # are theirs: 0x42FD40 'sub ecx, 28h; jmp 432EA0' passes on the two its callers push)
helpers = {}
for a, (size, pop) in funcs.items():
    h = frame_helper(a, size)
    if h is not None:
        helpers[a] = h
print('frame helpers: %s' % ', '.join('%08X (ebp = esp%+d)' % (a, h) for a, h in sorted(helpers.items())))

# arguments the callers of a caller-pop function push: the 'add esp, N' right after each direct call.  A function
# may ignore some (0x458940 checks an HRESULT and is given __FILE__ and __LINE__ it never reads); with fewer
# parameters than pushed, the decompiler gives the extra pushes to a call nearby
cleanups = {}
for a, (size, pop) in funcs.items():
    try:
        ins = list(md.disasm(pe.read(a, size), a))
    except Exception:
        continue
    at = {i.address: i for i in ins}
    pro = prologue_end(at.get, a)
    for k, i in enumerate(ins[:-1]):
        if i.mnemonic == 'call' and i.operands[0].type == x86.X86_OP_IMM and i.operands[0].imm in funcs and \
                funcs[i.operands[0].imm][1] == 0:
            n = ins[k + 1]
            add = n.operands[1].imm if n.mnemonic == 'add' and n.operands[0].type == x86.X86_OP_REG and \
                n.operands[0].reg == ESP and n.operands[1].type == x86.X86_OP_IMM else 0
            # the pushes right before (with only moves between): an add that removes more cleans up after an
            # earlier call too (0x46AC27 'lea ecx, [esp+18h]; call 427820' pushes nothing; the destructor was
            # given six parameters from such adds)
            pushes = 0
            for j in range(k - 1, -1, -1):
                if ins[j].address < pro:
                    break              # the prologue's 'push ecx' (room for a local) is no argument (0x4D4B11)
                m = ins[j].mnemonic
                if m == 'push':
                    pushes += 1
                elif not (m.startswith('mov') or m == 'lea' or m.startswith('fld') or m.startswith('fst')):
                    break
            if add > 4 * pushes:
                add = 0
            cleanups.setdefault(i.operands[0].imm, []).append(add)


def pushed_args(a):
    """the add esp right after its calls, when at least two are there and all agree (the compiler often cleans up
    later, and one add after two calls can clean up both)"""
    nz = [n for n in cleanups.get(a, []) if n]
    return nz[0] // 4 if len(nz) >= 2 and len(set(nz)) == 1 else 0


with open(sys.argv[3], 'w') as f:
    f.write('# address\tstack slots used\texact|lost\tslots read as dwords, never written'
            '\targuments callers push (commonest add esp / 4 after direct calls of a caller-pop function)'
            '\tslots only floats are read from or written to (k:f float, k:d double in k and k+1)'
            ' (tools/stackparams.py)\n')
    res = {a: list(analyse(a, funcs[a][0])) + [pushed_args(a)] for a in sorted(funcs)}
    # a tail jump passes the stack on: the target's parameters (and their kinds) are this function's too
    for _ in range(8):
        changed = False
        for a, ts in tails.items():
            for t in ts:
                n, how, dw, fl, pa = res[a]
                tn, thow, tdw, tfl, tpa = res[t]
                if tn > n or (tn == n and not fl and tfl) or (not pa and tpa) or set(tdw) - set(dw):
                    pop = funcs[a][1]
                    m = max(n, tn) if not pop else max(n, min(tn, pop // 4))   # a callee-pop one has no more
                    res[a] = [m, how if thow == 'exact' else thow, sorted(x for x in set(dw) | set(tdw) if x < max(m, 1)),
                              fl or [x for x in tfl if int(x.split(':')[0]) < m], pa or tpa]
                    if res[a] != [n, how, dw, fl, pa]:
                        changed = True
        if not changed:
            break
    # prototypes set by hand (symbols/GAME_protos.tsv): their parameter count
    mp = sys.argv[2].replace('_functions.tsv', '_protos.tsv')
    if os.path.exists(mp):
        for l in open(mp):
            q = l.rstrip('\n').split('\t')
            if l[0] != '#' and len(q) > 3 and int(q[0], 16) in res:
                ps = re.search(r'\((.*)\)', q[3]).group(1).strip()
                k = 0 if ps in ('', 'void') else ps.count(',') + 1
                k -= q[1] in ('thiscall', 'fastcall')
                k -= q[1] == 'fastcall' and k > 0
                res[int(q[0], 16)] = [k, 'exact', list(range(k)), [], 0]
    for a in sorted(funcs):
        n, how, dw, fl, pa = res[a]
        f.write('%08X\t%d\t%s\t%s\t%d\t%s\n' % (a, n, how, ','.join(map(str, dw)), pa, ','.join(fl)))
print('done')
