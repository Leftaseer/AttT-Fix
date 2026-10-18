#!/usr/bin/env python3
"""Register inputs of every function from the machine code: registers read on some path from the entry before
being written (push/pop saves are not reads; calls clobber EAX/ECX/EDX).  Detects MSVC /LTCG custom conventions.
usage: regparams.py EXE BINFEAT.json OUT.tsv   ->  ADDR <tab> regs (e.g. ECX,EAX) <tab> ret-pop-bytes"""
import sys, json; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__))); from pe import PE
import capstone
from capstone import x86_const as X
p = PE(sys.argv[1]); bf = {int(k, 16): v for k, v in json.load(open(sys.argv[2])).items()}
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True
FULL = {}
for full, subs in {'EAX': ('eax', 'ax', 'al', 'ah'), 'ECX': ('ecx', 'cx', 'cl', 'ch'), 'EDX': ('edx', 'dx', 'dl', 'dh'),
                   'EBX': ('ebx', 'bx', 'bl', 'bh'), 'ESI': ('esi', 'si'), 'EDI': ('edi', 'di'), 'EBP': ('ebp', 'bp')}.items():
    for s in subs: FULL[s] = full
BIT = {'EAX': 1, 'ECX': 2, 'EDX': 4, 'EBX': 8, 'ESI': 16, 'EDI': 32, 'EBP': 64}
def regs(i, names):
    return set(FULL[i.reg_name(r)] for r in names if i.reg_name(r) in FULL)
out = open(sys.argv[3], 'w')
for start in sorted(bf):
    size = bf[start]['size']; end = start + size
    code = p.read(start, size)
    if not code: continue
    ins = {}
    for i in md.disasm(code, start): ins[i.address] = i
    inputs = 0; retpop = set()
    seen = set(); work = [(start, 0)]; steps = 0
    while work and steps < 20000:
        a, w = work.pop()
        while True:
            steps += 1
            if (a, w) in seen or a not in ins: break
            seen.add((a, w)); i = ins[a]
            m = i.mnemonic
            try:
                rd, wr = i.regs_access()
            except Exception:
                break
            r = regs(i, rd); wrr = regs(i, wr)
            if m == 'push' and i.operands[0].type == X.X86_OP_REG: r = set()
            if m == 'pop': r = set()
            if m in ('xor', 'sub', 'sbb') and len(i.operands) == 2 and i.operands[0].type == X.X86_OP_REG and i.operands[1].type == X.X86_OP_REG and i.operands[0].reg == i.operands[1].reg:
                r = set() if m != 'sbb' else r
            if m == 'call': r = set()
            for x in r:
                if not w & BIT[x]: inputs |= BIT[x]
            for x in wrr: w |= BIT[x]
            if m == 'call': w |= BIT['EAX'] | BIT['ECX'] | BIT['EDX']
            if m in ('ret', 'retf'):
                retpop.add(i.operands[0].imm if i.operands else 0); break
            if m == 'int3' or m == 'hlt': break
            if m == 'jmp':
                o = i.operands[0]
                if o.type == X.X86_OP_IMM and start <= o.imm < end: a = o.imm; continue
                break  # tail call or switch: stop
            if m.startswith('j') or m.startswith('loop'):
                o = i.operands[0]
                if o.type == X.X86_OP_IMM and start <= o.imm < end: work.append((o.imm, w))
            a = a + i.size
    names = [n for n, b in BIT.items() if inputs & b]
    out.write('%08X\t%s\t%s\n' % (start, ','.join(names), ','.join(str(x) for x in sorted(retpop))))
out.close()
