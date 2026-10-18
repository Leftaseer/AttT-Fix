#!/usr/bin/env python3
"""Constructors and object sizes from vtable stores and operator new call sites.
usage: ctors.py EXE RTTI.json BINFEAT.json SYMS.sym OUT_SYM OUT_SIZES.json"""
import sys, json, collections; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__))); from pe import PE
import capstone
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG
p = PE(sys.argv[1]); C = json.load(open(sys.argv[2])); bf = {int(k, 16): v for k, v in json.load(open(sys.argv[3])).items()}
syms = {}
for l in open(sys.argv[4], encoding='utf-8'):
    if l[0] in '#S' or not l.strip(): continue
    b = l.split('#')[0].split(None, 2); syms[int(b[0], 16)] = b[2].strip()
vt0 = {}
for c in C:
    for v in c['vtables']:
        vt0[int(v['vt'], 16)] = (c['name'], v['offset'])
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True
new_imp = [a for a, (d, n) in p.imports.items() if n == '??2@YAPAXI@Z']
new_funcs = set()
for a, f in bf.items():  # local wrappers: jmp [__imp_new]
    b = p.read(a, 6)
    if b and b[:2] == b'\xff\x25' and p.u32(a + 2) in new_imp: new_funcs.add(a)
stores = collections.defaultdict(set)  # func -> classes whose primary vtable it stores
sizes = collections.defaultdict(collections.Counter)
newcalls = {}
for a in sorted(bf):
    f = bf[a]
    code = p.read(a, f['size'])
    last_push = None; after_new = None; ins = list(md.disasm(code, a))
    for k, i in enumerate(ins):
        if i.mnemonic == 'mov' and len(i.operands) == 2 and i.operands[0].type == X86_OP_MEM and i.operands[1].type == X86_OP_IMM:
            v = i.operands[1].imm & 0xffffffff
            if v in vt0 and vt0[v][1] == 0 and i.operands[0].mem.disp == 0: stores[a].add(vt0[v][0])
        if i.mnemonic == 'push' and i.operands[0].type == X86_OP_IMM: last_push = i.operands[0].imm
        if i.mnemonic == 'call':
            o = i.operands[0]
            isnew = (o.type == X86_OP_MEM and (o.mem.disp & 0xffffffff) in new_imp) or (o.type == X86_OP_IMM and o.imm in new_funcs)
            if isnew and last_push:
                # the first direct call with ecx = eax (result of new) within the next 12 instructions
                for j in range(k + 1, min(k + 14, len(ins))):
                    x = ins[j]
                    if x.mnemonic == 'call' and x.operands[0].type == X86_OP_IMM:
                        newcalls[(a, i.address)] = (last_push, x.operands[0].imm); break
            last_push = None if i.mnemonic == 'call' else last_push
out = {}
for (site, at), (sz, ctor) in newcalls.items():
    cls = stores.get(ctor)
    if cls and len(cls) >= 1:
        # most derived = the class with the most bases
        bases = {c['name']: len(c['bases']) for c in C}
        c = max(cls, key=lambda x: bases.get(x, 0))
        sizes[c][sz] += 1
        out[ctor] = c
res_sizes = {c: cnt.most_common(1)[0][0] for c, cnt in sizes.items()}
with open(sys.argv[5], 'w') as f:
    for ctor, c in sorted(out.items()):
        leaf = c.split('::')[-1].split('<')[0]
        if ctor in syms and not syms[ctor].startswith(('FUN_',)): continue
        f.write('%08X f %s::%s # ctor\n' % (ctor, c, leaf))
json.dump(res_sizes, open(sys.argv[6], 'w'), indent=1, sort_keys=True)
print(len(out), 'constructors,', len(res_sizes), 'class sizes')
