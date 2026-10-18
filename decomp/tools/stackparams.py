#!/usr/bin/env python3
"""Stack parameters each function really uses, from the machine code: follows ESP through the function
(push/pop, sub/add esp, calls with the ret pop of the callee from functions.tsv) and EBP frames, and records the
highest stack slot above the return address that is read, written or addressed.  The decompiler misses
parameters a function only passes on to a call (Lua's lua_pushlstring takes (L, s, len) and hands s and len to
luaS_newlstr untouched), and every caller is then decompiled without those arguments.

usage: stackparams.py EXE symbols/GAME_functions.tsv OUT.tsv [AUTO.jsonl.protos (conventions of imports)]
OUT: address, number of 4-byte stack slots used (0 if none), 'exact' or 'lost' (ESP could not be followed
everywhere, e.g. after an indirect call with unknown cleanup: the count is a lower bound)."""
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
    funcs[int(q[0], 16)] = (int(q[1]), int(q[3] or 0))
imports = {}           # IAT slot -> bytes the imported function pops (from AutoExport's .protos, optional)
if len(sys.argv) > 4:
    W8 = {'double', 'longlong', 'ulonglong', 'undefined8', 'qword'}
    for l in open(sys.argv[4], encoding='utf-8'):
        q = l.rstrip('\n').split('\t')
        if len(q) > 6 and q[6] == 'import':
            ps = [x.strip().rsplit(' ', 1)[0] for x in q[4].split(',') if x.strip()] if q[4] else []
            if q[1] == '__thiscall':
                ps = ps[1:]
            n = sum(8 if t in W8 else 4 for t in ps)
            imports[int(q[0], 16)] = n if q[1] in ('__stdcall', '__thiscall') and q[5] != 'true' else 0
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
ESP, EBP = x86.X86_REG_ESP, x86.X86_REG_EBP


def analyse(start, size):
    code = {}
    try:
        for i in md.disasm(pe.read(start, size), start):
            code[i.address] = i
    except Exception:
        return 0, 'lost'
    top = 0                    # highest byte offset above the return address seen (exclusive)
    lost = False
    todo = [(start, 0, None)]  # address, esp delta (0 = at the return address), ebp delta or None
    pushed = 0                 # bytes pushed since the last call: the arguments of the next one
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
                    # otherwise the callee popped what was pushed for it
                    nxt = code.get(i.address + i.size)
                    caller_cleans = nxt is not None and nxt.mnemonic == 'add' and nxt.operands[0].type == x86.X86_OP_REG \
                        and nxt.operands[0].reg == ESP
                    if d is not None and not caller_cleans:
                        d += pushed
                pushed = 0
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
    return slots, 'lost' if lost else 'exact'


with open(sys.argv[3], 'w') as f:
    f.write('# address\tstack slots used\texact|lost (tools/stackparams.py)\n')
    for a in sorted(funcs):
        n, how = analyse(a, funcs[a][0])
        f.write('%08X\t%d\t%s\n' % (a, n, how))
print('done')
