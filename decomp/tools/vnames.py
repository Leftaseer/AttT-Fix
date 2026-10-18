#!/usr/bin/env python3
"""Names from RTTI: vtables, virtual functions (owner = most basic class using the function in that slot),
scalar/vector deleting destructors and destructors, constructors (functions storing a vtable).
usage: vnames.py EXE RTTI.json OUT.sym"""
import sys, json, collections, struct; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__))); from pe import PE
import capstone
from capstone.x86 import X86_OP_IMM, X86_OP_MEM
p = PE(sys.argv[1]); C = json.load(open(sys.argv[2])); t0, t1 = p.text_range()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True
bases = {c['name']: set(b['name'] for b in c['bases']) for c in C}
delete_imp = [a for a, (d, n) in p.imports.items() if n in ('??3@YAXPAX@Z',)]
vdelete_imp = [a for a, (d, n) in p.imports.items() if n in ('??_V@YAXPAX@Z',)]
purecall = [a for a, (d, n) in p.imports.items() if n == '_purecall']
uses = collections.defaultdict(list)  # func -> [(class, suboffset, slot)]
vts = {}
for c in C:
    for v in c['vtables']:
        vts[int(v['vt'], 16)] = (c['name'], v['offset'])
        for i, f in enumerate(v['funcs']): uses[int(f, 16)].append((c['name'], v['offset'], i))
def short(n): return n
out = {}
def put(a, kind, name, why):
    if a not in out: out[a] = (kind, name, why)
for vt, (cn, off) in vts.items():
    put(vt, 'd', '%s::vftable%s' % (cn, '' if off == 0 else '_%X' % off), 'rtti')
def insns(a, n=40):
    code = p.read(a, 0x200)
    res = []
    for i in md.disasm(code, a):
        res.append(i)
        if len(res) >= n or i.mnemonic in ('ret', 'int3'): break
    return res
def calls_of(a):
    r = []
    for i in insns(a, 60):
        if i.mnemonic == 'call':
            o = i.operands[0]
            if o.type == X86_OP_IMM: r.append(o.imm)
            elif o.type == X86_OP_MEM and o.mem.base == 0: r.append(('imp', o.mem.disp & 0xffffffff))
            elif o.type == X86_OP_MEM: r.append(('ind',))
    return r
def is_deleting_dtor(a):
    cs = calls_of(a)
    imps = [c[1] for c in cs if isinstance(c, tuple) and c[0] == 'imp']
    direct = [c for c in cs if isinstance(c, int)]
    if any(i in delete_imp or i in vdelete_imp for i in imps): return direct
    # operator delete may be a local thunk
    for d in direct:
        ii = insns(d, 2)
        if ii and ii[0].mnemonic == 'jmp' and ii[0].operands[0].type == X86_OP_MEM and (ii[0].operands[0].mem.disp & 0xffffffff) in delete_imp:
            return [x for x in direct if x != d]
    return None
for f, us in uses.items():
    if f in purecall or (p.read(f, 6) or b'')[:2] == b'\xff\x25' and p.u32(f + 2) in purecall:
        put(f, 'f', '_purecall', 'rtti'); continue
    classes = set(u[0] for u in us)
    owner = None
    for c in classes:
        if all(c in bases.get(o, ()) for o in classes): owner = c; break
    if owner is None:
        # function shared by unrelated classes (identical code folded by the linker)
        put(f, 'f', 'shared_vf_%s_%d' % (sorted(classes)[0].replace('::', '_').replace('<', '_').replace('>', '_').replace(' ', '').replace(',', '_').replace('*', 'P'), us[0][2]), 'rtti-shared'); continue
    slot = min(u[2] for u in us if u[0] == owner)
    off = min(u[1] for u in us if u[0] == owner)
    leaf = owner.split('::')[-1].split('<')[0]
    dd = is_deleting_dtor(f) if slot == 0 or True else None
    if dd is not None and slot <= 2:
        put(f, 'f', "%s::`scalar deleting destructor'" % owner, 'rtti-ddtor')
        if len(dd) == 1: put(dd[0], 'f', '%s::~%s' % (owner, leaf), 'rtti-dtor')
        continue
    put(f, 'f', '%s::vf%d%s' % (owner, slot, '' if off == 0 else '_%X' % off), 'rtti')
# constructors/destructors: functions storing a vtable address (mov dword [reg], vt)
starts = sorted(int(l.split()[0], 16) for l in open(sys.argv[3] + '.starts')) if False else None
with open(sys.argv[3], 'w') as fo:
    for a in sorted(out):
        k, n, w = out[a]; fo.write('%08X %s %s # %s\n' % (a, k, n, w))
print(len(out), 'symbols', collections.Counter(w for k, n, w in out.values()))
