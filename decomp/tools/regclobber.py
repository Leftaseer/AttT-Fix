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
    # a register saved first thing and restored before the one ret is left as it was (_alloca_probe 0x5E4080:
    # 'push ecx; lea ecx, [esp+4] ... pop ecx; xchg esp, eax; ...; ret' keeps ECX, which its callers' 'this' is in)
    ins = list(md.disasm(code, a))
    rets = [k for k, i in enumerate(ins) if i.mnemonic.startswith('ret')]
    if ins and ins[0].mnemonic == 'push' and ins[0].op_str in ('eax', 'ecx', 'edx') and len(rets) == 1:
        reg = ins[0].op_str
        # (not 'push ecx' making room for a local, written and popped back: no store through ESP, no call before
        # the pop)
        def stores_esp(j):
            # (any access through ESP: capstone does not mark the x87 stores 'fstp [esp]' as writes)
            return j.mnemonic == 'call' or (j.mnemonic != 'lea' and any(
                o.type == capstone.x86_const.X86_OP_MEM and o.mem.base == capstone.x86_const.X86_REG_ESP
                for o in j.operands))
        for k in range(rets[0] - 1, 0, -1):
            j = ins[k]
            if j.mnemonic == 'pop' and j.op_str == reg:
                if not any(stores_esp(x) for x in ins[1:k]):
                    w.discard(FULL[reg])
                break
            try:
                if any(FULL.get(j.reg_name(r)) == FULL[reg] for r in j.regs_access()[1]) or j.mnemonic in ('call', 'jmp'):
                    break
            except Exception:
                break
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
