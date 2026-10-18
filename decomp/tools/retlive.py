#!/usr/bin/env python3
"""Which functions return something in EAX that their callers use: after each direct call, follow the caller's
code (both ways at branches, up to a limit) and see whether EAX is read before it is overwritten.  A ret of the
caller counts as a use (it may pass the value on).  The decompiler sometimes types such a function as void
(it saw no value being computed for EAX on the way out), and a replacement written that way would return garbage.

usage: retlive.py EXE symbols/GAME_functions.tsv OUT.tsv      (OUT: address of every function whose EAX is used)"""
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
    funcs[int(q[0], 16)] = (int(q[1]), set(x for x in q[2].split(',') if x))
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
EAX = {x86.X86_REG_EAX, x86.X86_REG_AX, x86.X86_REG_AL, x86.X86_REG_AH}

insns = {}          # address -> instruction, per function
for a, (size, _) in funcs.items():
    try:
        for i in md.disasm(pe.read(a, size), a):
            insns[i.address] = i
    except Exception:
        pass


def eax_used_after(addr, limit=80):
    """True if EAX may be read at addr (just after a call) before being fully overwritten."""
    todo, seen, n = [addr], set(), 0
    while todo:
        p = todo.pop()
        while True:
            if p in seen or n > limit:
                break
            seen.add(p)
            i = insns.get(p)
            if i is None:
                return True                         # left the known code: assume used
            n += 1
            m = i.mnemonic
            if m == 'xor' and len(i.operands) == 2 and i.op_str in ('eax, eax',):
                break                               # eax = 0
            if m == 'call':
                t = i.operands[0]
                if t.type == x86.X86_OP_IMM and 'EAX' in funcs.get(t.imm, (0, set()))[1]:
                    return True                     # passed on in EAX (LTCG)
                break                               # the next call sets EAX
            if m.startswith('ret'):
                return True
            try:
                rd, wr = i.regs_access()
            except Exception:
                return True
            if EAX & set(rd):
                return True
            if x86.X86_REG_EAX in wr:
                break
            if m == 'jmp':
                t = i.operands[0]
                if t.type == x86.X86_OP_IMM:
                    p = t.imm
                    continue
                return True                         # jump table / tail jump
            if m.startswith('j') or m.startswith('loop'):
                t = i.operands[0]
                if t.type == x86.X86_OP_IMM:
                    todo.append(t.imm)
            p = i.address + i.size
    return False


used = set()
for a, i in insns.items():
    if i.mnemonic == 'call' and i.operands[0].type == x86.X86_OP_IMM:
        t = i.operands[0].imm
        if t in funcs and t not in used and eax_used_after(a + i.size):
            used.add(t)
with open(sys.argv[3], 'w') as f:
    f.write('# functions whose result in EAX some caller uses (tools/retlive.py)\n')
    for a in sorted(used):
        f.write('%08X\n' % a)
print('%d of %d functions: EAX used by a caller' % (len(used), len(funcs)))
