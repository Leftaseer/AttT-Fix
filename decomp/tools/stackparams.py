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
pointer down to a byte)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import PE
import capstone
from capstone import x86

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
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
ESP, EBP = x86.X86_REG_ESP, x86.X86_REG_EBP


def analyse(start, size):
    code = {}
    try:
        for i in md.disasm(pe.read(start, size), start):
            code[i.address] = i
    except Exception:
        return 0, 'lost', ()
    top = 0                    # highest byte offset above the return address seen (exclusive)
    dword_read, written = set(), set()
    lost = False
    todo = [(start, 0, None)]  # address, esp delta (0 = at the return address), ebp delta or None
    pushed = 0                 # bytes pushed since the last call: the arguments of the next one
    run = 0                    # pushes right before, with only moves between them
    seen = {}
    steps = 0
    while todo:
        p, d, bp = todo.pop()
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
                    nxt = code.get(i.address + i.size)
                    caller_cleans = nxt is not None and nxt.mnemonic == 'add' and nxt.operands[0].type == x86.X86_OP_REG \
                        and nxt.operands[0].reg == ESP
                    if d is not None and not caller_cleans:
                        d += icall_pop[i.address] if icall_pop.get(i.address, -1) >= 0 else 4 * run
                pushed = 0
            # pushes right before the next instruction, with only moves between them
            run = run + 1 if m == 'push' else run if (m.startswith('mov') or m == 'lea' or m.startswith('fld') or
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
                break                  # tail jump or table
            if m.startswith('j') or m.startswith('loop'):
                if ops[0].type == x86.X86_OP_IMM:
                    todo.append((ops[0].imm, d, bp))
            p = i.address + i.size
    slots = max(0, (top - 4 + 3) // 4)
    return slots, 'lost' if lost else 'exact', sorted(dword_read - written)


# arguments the callers of a caller-pop function push: the 'add esp, N' right after each direct call.  A function
# may ignore some (0x458940 checks an HRESULT and is given __FILE__ and __LINE__ it never reads); with fewer
# parameters than pushed, the decompiler gives the extra pushes to a call nearby
cleanups = {}
for a, (size, pop) in funcs.items():
    try:
        ins = list(md.disasm(pe.read(a, size), a))
    except Exception:
        continue
    for k, i in enumerate(ins[:-1]):
        if i.mnemonic == 'call' and i.operands[0].type == x86.X86_OP_IMM and i.operands[0].imm in funcs and \
                funcs[i.operands[0].imm][1] == 0:
            n = ins[k + 1]
            add = n.operands[1].imm if n.mnemonic == 'add' and n.operands[0].type == x86.X86_OP_REG and \
                n.operands[0].reg == ESP and n.operands[1].type == x86.X86_OP_IMM else 0
            cleanups.setdefault(i.operands[0].imm, []).append(add)


def pushed_args(a):
    """the add esp right after its calls, when at least two are there and all agree (the compiler often cleans up
    later, and one add after two calls can clean up both)"""
    nz = [n for n in cleanups.get(a, []) if n]
    return nz[0] // 4 if len(nz) >= 2 and len(set(nz)) == 1 else 0


with open(sys.argv[3], 'w') as f:
    f.write('# address\tstack slots used\texact|lost\tslots read as dwords, never written'
            '\targuments callers push (commonest add esp / 4 after direct calls of a caller-pop function)'
            ' (tools/stackparams.py)\n')
    for a in sorted(funcs):
        n, how, dw = analyse(a, funcs[a][0])
        f.write('%08X\t%d\t%s\t%s\t%d\n' % (a, n, how, ','.join(map(str, dw)), pushed_args(a)))
print('done')
