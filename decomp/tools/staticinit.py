# Collect constant stores to absolute addresses done by code (dynamic initializers), then find
# Lunar-style method tables {name, ?, func, adj} (stride 16) and print them.
import sys, json; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__))); from pe import PE
import capstone
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG
p = PE(sys.argv[1]); t0, t1 = p.text_range()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True; md.skipdata = True
code = p.read(t0, t1 - t0)
M = {}; W = {}  # addr -> value, addr -> writer insn address
regs = {}
for i in md.disasm(code, t0):
    if i.id == 0: regs = {}; continue
    if i.mnemonic in ('ret', 'jmp', 'call', 'int3') or i.mnemonic.startswith('j'):
        regs = {}; continue
    ops = i.operands
    if i.mnemonic == 'mov' and len(ops) == 2:
        d, s = ops
        if d.type == X86_OP_REG:
            if s.type == X86_OP_IMM: regs[d.reg] = s.imm & 0xffffffff
            else: regs.pop(d.reg, None)
            continue
        if d.type == X86_OP_MEM and d.mem.base == 0 and d.mem.index == 0 and d.size == 4:
            v = s.imm & 0xffffffff if s.type == X86_OP_IMM else regs.get(s.reg) if s.type == X86_OP_REG else None
            if v is not None: M[d.mem.disp & 0xffffffff] = v; W[d.mem.disp & 0xffffffff] = i.address
            continue
    elif i.mnemonic == 'xor' and len(ops) == 2 and ops[0].type == X86_OP_REG and ops[1].type == X86_OP_REG and ops[0].reg == ops[1].reg:
        regs[ops[0].reg] = 0; continue
    # any other write to a register invalidates it
    try:
        _, w = i.regs_access()
        for r in w: regs.pop(r, None)
    except Exception: regs = {}
out = []
seen = set()
for a in sorted(M):
    if a in seen: continue
    ents = []; b = a
    while True:
        n = M.get(b); f = M.get(b + 8)
        if n is None or f is None or not (t0 <= f < t1): break
        s = p.cstr(n, 64)
        if not s or not s.replace('_', '').isalnum(): break
        ents.append((s, f)); seen.add(b); b += 16
    if len(ents) >= 1:
        out.append({'table': '%08X' % a, 'writer': '%08X' % W[a], 'methods': [[s, '%08X' % f] for s, f in ents]})
json.dump(out, open(sys.argv[2], 'w'), indent=0)
print(len(out), 'tables', sum(len(t['methods']) for t in out), 'methods')
