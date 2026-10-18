#!/usr/bin/env python3
"""Find C functions registered into Lua: lua_pushcclosure(L, f, n) followed by lua_setfield(L, idx, "name").
usage: luaglobals.py EXE PUSHCCLOSURE SETFIELD OUT.tsv"""
import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__))); from pe import PE
import capstone
from capstone.x86 import X86_OP_IMM, X86_OP_REG, X86_OP_MEM
p = PE(sys.argv[1]); pcc = int(sys.argv[2], 16); sf = int(sys.argv[3], 16)
t0, t1 = p.text_range()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True; md.skipdata = True
pushes = []; pend = None; regs = {}
out = []
for i in md.disasm(p.read(t0, t1 - t0), t0):
    if i.id == 0: pushes = []; pend = None; continue
    m = i.mnemonic
    if m == 'push':
        o = i.operands[0]
        if o.type == X86_OP_IMM: pushes.append(o.imm & 0xffffffff)
        elif o.type == X86_OP_REG: pushes.append(regs.get(o.reg))
        else: pushes.append(None)
        continue
    if m == 'mov' and i.operands[0].type == X86_OP_REG:
        s = i.operands[1]
        regs[i.operands[0].reg] = (s.imm & 0xffffffff) if s.type == X86_OP_IMM else None
        continue
    if m == 'call' and i.operands[0].type == X86_OP_IMM:
        t = i.operands[0].imm
        if t == pcc and len(pushes) >= 3:
            pend = (pushes[-2], i.address)
        elif t == sf and len(pushes) >= 3 and pend:
            name = p.cstr(pushes[-3] or 0, 80); idx = pushes[-2]
            if name and pend[0] and t0 <= pend[0] < t1:
                idxs = {0xffffd8ee: 'G', 0xfffffffe: '-2', 0xffffffff: '-1', 0xfffffffd: '-3'}.get(idx, '%s' % idx)
                out.append((pend[0], name, idxs, i.address))
            pend = None
        pushes = []
        continue
    if m in ('ret', 'jmp') or m.startswith('j'): pushes = []; pend = None
with open(sys.argv[4], 'w') as f:
    for fn, name, idx, at in out: f.write('%08X\t%s\t%s\t%08X\n' % (fn, name, idx, at))
print(len(out), 'registrations,', len(set(o[0] for o in out)), 'functions')
