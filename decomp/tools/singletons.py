#!/usr/bin/env python3
"""Find CSingleton<T>::Instance() functions: 'if (!m_instance) m_instance = new T' with the object size, the
constructor and the class (from the vtables the constructor stores).  Writes names for the function, the
instance variable and the constructor.  usage: singletons.py EXE RTTI.json BINFEAT.json OUT.sym"""
import sys, os, json, re; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from pe import PE
import capstone
from capstone.x86 import X86_OP_IMM, X86_OP_MEM
p = PE(sys.argv[1]); C = json.load(open(sys.argv[2])); bf = {int(k, 16): v for k, v in json.load(open(sys.argv[3])).items()}
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True
vt = {}
nbases = {c['name']: len(c['bases']) for c in C}
for c in C:
    for v in c['vtables']: vt[int(v['vt'], 16)] = c['name']
new_imp = [a for a, (d, n) in p.imports.items() if n == '??2@YAPAXI@Z']
new_thunks = set(a for a in bf if (p.read(a, 6) or b'')[:2] == b'\xff\x25' and p.u32(a + 2) in new_imp)
def classes_stored(f):
    out = set()
    if f not in bf: return out
    for i in md.disasm(p.read(f, min(bf[f]['size'], 0x400)), f):
        if i.mnemonic == 'mov' and len(i.operands) == 2 and i.operands[0].type == X86_OP_MEM and i.operands[1].type == X86_OP_IMM:
            v = i.operands[1].imm & 0xffffffff
            if v in vt: out.add(vt[v])
    return out
out = []
for a in sorted(bf):
    if bf[a]['size'] > 0x140: continue
    ins = list(md.disasm(p.read(a, bf[a]['size']), a))[:40]
    g = None; size = None; ctor = None; newseen = False
    for k, i in enumerate(ins):
        if g is None and i.mnemonic == 'mov' and len(i.operands) == 2 and i.operands[1].type == X86_OP_MEM and \
                i.operands[1].mem.base == 0 and i.operands[1].mem.index == 0 and p.sec(i.operands[1].mem.disp & 0xffffffff) == '.data':
            g = i.operands[1].mem.disp & 0xffffffff
        if i.mnemonic == 'push' and i.operands[0].type == X86_OP_IMM and not newseen: size = i.operands[0].imm
        if i.mnemonic == 'call' and i.operands[0].type == X86_OP_IMM:
            if i.operands[0].imm in new_thunks: newseen = True; continue
            if newseen and ctor is None: ctor = i.operands[0].imm; break
    if not (g and size and ctor and newseen): continue
    # the result must be stored back into the same global
    if not any(i.mnemonic == 'mov' and i.operands[0].type == X86_OP_MEM and (i.operands[0].mem.disp & 0xffffffff) == g for i in ins):
        continue
    cls = classes_stored(ctor)
    if not cls: continue
    c = max(cls, key=lambda x: nbases.get(x, 0))
    if c.startswith('CSingleton<') or c.startswith('Singleton<'):
        c = c[c.index('<') + 1:-1]
    out.append((a, c, g, size, ctor))
with open(sys.argv[4], 'w') as f:
    for a, c, g, size, ctor in out:
        f.write('%08X f %s::Instance # singleton, new %#x\n' % (a, c, size))
        f.write('%08X d %s::m_instance # singleton\n' % (g, c))
        f.write('%08X f %s::%s # singleton ctor\n' % (ctor, c, c.split('::')[-1].split('<')[0]))
print(len(out), 'singletons:', ', '.join(sorted(set(o[1] for o in out))))
