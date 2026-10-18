#!/usr/bin/env python3
"""Volatile registers (EAX/ECX/EDX) each function may change, through its callees too.  /LTCG code sometimes
relies on a callee leaving ECX/EDX/EAX intact, so a replacement must preserve what the original preserved.
usage: regclobber.py EXE BINFEAT.json OUT.tsv   ->  ADDR <tab> clobbered (e.g. EAX,ECX)"""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from pe import PE
import capstone
p = PE(sys.argv[1]); bf = {int(k, 16): v for k, v in json.load(open(sys.argv[2])).items()}
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True
FULL = {}
for full, subs in {'EAX': ('eax', 'ax', 'al', 'ah'), 'ECX': ('ecx', 'cx', 'cl', 'ch'), 'EDX': ('edx', 'dx', 'dl', 'dh')}.items():
    for s in subs: FULL[s] = full
ALL = {'EAX', 'ECX', 'EDX'}
own = {}; calls = {}
for a in sorted(bf):
    w = set(); cs = set(); ind = False
    code = p.read(a, bf[a]['size']) or b''
    for i in md.disasm(code, a):
        if i.mnemonic == 'call':
            o = i.operands[0]
            if o.type == capstone.x86_const.X86_OP_IMM and o.imm in bf: cs.add(o.imm)
            else: ind = True
            continue
        if i.mnemonic == 'jmp':
            o = i.operands[0]
            if o.type == capstone.x86_const.X86_OP_IMM:
                if not (a <= o.imm < a + bf[a]['size']):
                    if o.imm in bf: cs.add(o.imm)
                    else: ind = True
            else: ind = True
            continue
        try:
            _, wr = i.regs_access()
        except Exception:
            continue
        for r in wr:
            n = i.reg_name(r)
            if n in FULL: w.add(FULL[n])
    if ind: w |= ALL
    own[a] = w; calls[a] = cs
clob = dict(own)
changed = True
while changed:
    changed = False
    for a in bf:
        s = clob[a]
        if s == ALL: continue
        n = set(s)
        for c in calls[a]: n |= clob.get(c, ALL)
        if n != s: clob[a] = n; changed = True
with open(sys.argv[3], 'w') as f:
    for a in sorted(clob): f.write('%08X\t%s\n' % (a, ','.join(sorted(clob[a]))))
import collections
print(collections.Counter(','.join(sorted(v)) for v in clob.values()))
