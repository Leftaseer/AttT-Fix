#!/usr/bin/env python3
"""Binary-side features per function: strings referenced, call targets, data refs, size.
usage: binfeat.py EXE FUNCS.tsv OUT.json   (FUNCS.tsv: first column = entry address in hex)"""
import sys, json; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__))); from pe import PE
import capstone
from capstone.x86 import X86_OP_IMM, X86_OP_MEM
p = PE(sys.argv[1]); t0, t1 = p.text_range()
starts = sorted(set(int(l.split('\t')[0], 16) for l in open(sys.argv[2]) if l.strip() and l[0] in '0123456789abcdefABCDEF'))
starts = [s for s in starts if t0 <= s < t1]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True
res = {}
for k, s in enumerate(starts):
    e = starts[k + 1] if k + 1 < len(starts) else t1
    code = p.read(s, e - s)
    f = {'size': e - s, 'strings': [], 'calls': [], 'data': [], 'icalls': [], 'n': 0}
    for i in md.disasm(code, s):
        f['n'] += 1
        if i.mnemonic == 'int3': break
        for o in i.operands:
            v = None
            if o.type == X86_OP_IMM: v = o.imm & 0xffffffff
            elif o.type == X86_OP_MEM and o.mem.base == 0 and o.mem.index == 0: v = o.mem.disp & 0xffffffff
            if v is None: continue
            if i.mnemonic == 'call' and o.type == X86_OP_IMM: f['calls'].append(v); continue
            if i.mnemonic == 'call' and v in p.imports: f['calls'].append('%s!%s' % p.imports[v]); continue
            if v in p.imports: f['icalls'].append('%s!%s' % p.imports[v]); continue
            sec = p.sec(v)
            if sec in ('.rdata', '.data'):
                st = p.cstr(v, 200)
                if st and len(st) >= 1: f['strings'].append(st)
                else: f['data'].append(v)
            elif sec == '.text' and i.mnemonic != 'call' and not i.mnemonic.startswith('j'):
                f['data'].append(v)
    res['%08X' % s] = f
json.dump(res, open(sys.argv[3], 'w'))
print(len(res), 'functions')
