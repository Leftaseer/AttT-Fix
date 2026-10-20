#!/usr/bin/env python3
"""Facts about every indirect call (virtual calls, function pointers) from the machine code, for
ghidra/ICallOverride.java: the decompiler gives such a call its default prototype and loses the object passed in
ECX ('(**(code **)*p)(1)' for 'mov ecx, esi; call [eax+4]' with this = esi).

For each 'call reg' / 'call [mem]' (not an import slot) inside a function:
  ecx      1 if ECX holds a value set for the call: written after the last call before it (walking back in address
           order), or the function's own ECX input when no call or write comes first; 0 if a call clobbered it
  cleanup  N of an 'add esp, N' right after the call (a caller-pop callee), -1 if there is none
  pushes   pushes right before the call with only moves between them (its arguments when nothing is nested)

usage: icalls.py EXE symbols/GAME_functions.tsv OUT.tsv"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import PE
import capstone
from capstone import x86

pe = PE(sys.argv[1])
funcs = []
for l in open(sys.argv[2]):
    if l[0] == '#':
        continue
    q = l.rstrip('\n').split('\t')
    funcs.append((int(q[0], 16), int(q[1]), 'ECX' in q[2].split(',')))
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
slots = set(pe.imports)
ECXS = {x86.X86_REG_ECX, x86.X86_REG_CX, x86.X86_REG_CL, x86.X86_REG_CH}
MOVES = ('mov', 'lea', 'fld', 'fst', 'fild', 'fistp', 'movs', 'movz')

with open(sys.argv[3], 'w') as f:
    f.write('# call address\tfunction\tecx set (1/0)\tadd esp after (-1: none)\tpushes right before\n')
    n = 0
    for start, size, ecx_in in funcs:
        try:
            ins = list(md.disasm(pe.read(start, size), start))
        except Exception:
            continue
        for k, i in enumerate(ins):
            if i.mnemonic != 'call':
                continue
            op = i.operands[0]
            if op.type == x86.X86_OP_IMM:
                continue
            if op.type == x86.X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0 and op.mem.disp in slots:
                continue
            ecx = None
            for j in range(k - 1, -1, -1):
                p = ins[j]
                if p.mnemonic == 'call':
                    ecx = 0
                    break
                try:
                    w = p.regs_access()[1]
                except Exception:
                    w = []
                if any(r in ECXS for r in w):
                    ecx = 1
                    break
            if ecx is None:
                ecx = 1 if ecx_in else 0
            nxt = ins[k + 1] if k + 1 < len(ins) else None
            cleanup = -1
            if nxt is not None and nxt.mnemonic == 'add' and nxt.operands[0].type == x86.X86_OP_REG and \
                    nxt.operands[0].reg == x86.X86_REG_ESP and nxt.operands[1].type == x86.X86_OP_IMM:
                cleanup = nxt.operands[1].imm
            pushes = 0
            for j in range(k - 1, -1, -1):
                m = ins[j].mnemonic
                if m == 'push':
                    pushes += 1
                elif not m.startswith(MOVES):
                    break
            f.write('%08X\t%08X\t%d\t%d\t%d\n' % (i.address, start, ecx, cleanup, pushes))
            n += 1
print('%d indirect calls' % n)
