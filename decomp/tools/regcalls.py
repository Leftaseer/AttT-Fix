#!/usr/bin/env python3
"""Generic registration finder: calls whose pushed immediates include a string and a code pointer.
usage: regcalls.py EXE OUT.tsv   (callee, name, func, site); prints callees by count."""
import sys, collections; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__))); from pe import PE
import capstone
from capstone.x86 import X86_OP_IMM, X86_OP_REG
p = PE(sys.argv[1]); t0, t1 = p.text_range()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True; md.skipdata = True
vals = []; regs = {}; out = []
def isstr(v):
    if not v or p.sec(v) not in ('.rdata', '.data'): return None
    s = p.cstr(v, 100)
    return s if s and len(s) >= 2 and s.replace('_', '').replace('.', '').isalnum() else None
for i in md.disasm(p.read(t0, t1 - t0), t0):
    if i.id == 0: vals = []; regs = {}; continue
    m = i.mnemonic; ops = i.operands
    if m == 'push':
        o = ops[0]
        v = (o.imm & 0xffffffff) if o.type == X86_OP_IMM else regs.get(o.reg) if o.type == X86_OP_REG else None
        if v is not None: vals.append(v)
        continue
    if m in ('mov', 'lea') and ops and ops[0].type == X86_OP_REG:
        s = ops[1]
        regs[ops[0].reg] = (s.imm & 0xffffffff) if (m == 'mov' and s.type == X86_OP_IMM) else None
        if m == 'mov' and s.type == X86_OP_IMM: vals.append(s.imm & 0xffffffff)
        continue
    if m == 'mov' and ops and ops[1].type == X86_OP_IMM:
        vals.append(ops[1].imm & 0xffffffff); continue
    if m == 'call':
        callee = ops[0].imm if ops[0].type == X86_OP_IMM else None
        ss = [v for v in vals if isstr(v)]; fs = [v for v in vals if t0 <= v < t1]
        if callee and len(ss) == 1 and len(fs) == 1:
            out.append((callee, isstr(ss[0]), fs[0], i.address))
        vals = []; continue
    if m in ('ret', 'jmp') or m.startswith('j'): vals = []; regs = {}
cnt = collections.Counter(o[0] for o in out)
for c, n in cnt.most_common(25): print('%08X %d  e.g. %s' % (c, n, [o[1] for o in out if o[0] == c][:5]))
with open(sys.argv[2], 'w') as f:
    for c, s, fn, at in out: f.write('%08X\t%s\t%08X\t%08X\n' % (c, s, fn, at))
