#!/usr/bin/env python3
"""MSVC RTTI recovery: classes, base classes, vtables and their slots.  usage: rtti.py EXE OUT.json"""
import sys, json, struct, re; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__))); from pe import PE
p = PE(sys.argv[1]); t0, t1 = p.text_range()
import subprocess
_dm = {}
def demangle_td(n):  # ".?AVCFoo@NBar@@" -> "NBar::CFoo" (llvm-undname)
    if n in _dm: return _dm[n]
    out = subprocess.run(['llvm-undname'], input='??_R0' + n[1:] + '@8\n', capture_output=True, text=True).stdout.strip().splitlines()
    r = out[-1] if out else ''
    m = re.match(r"(?:class|struct|union) (.*) `RTTI Type Descriptor'$", r)
    if m:
        _dm[n] = re.sub(r'\b(class|struct|enum|union) ', '', m.group(1)); return _dm[n]
    return demangle_td_old(n)
def demangle_td_old(n):
    m = re.match(r'\.\?A[VUW](.*)@@$', n)
    if not m: return n
    body = m.group(1)
    if '?$' in body or '?' in body:  # templates: keep raw-ish
        parts = body.split('@')
    else:
        parts = body.split('@')
    parts = [x for x in parts if x]
    return '::'.join(reversed(parts))
tds = {}
def td(va):
    if va in tds: return tds[va]
    nm = p.cstr(va + 8, 256)
    tds[va] = demangle_td(nm) if nm else None
    return tds[va]
classes = {}
vtables = []
rdata = [s for s in p.secs if s[0] == '.rdata'][0]
for r in p.relocs:
    if p.sec(r) != '.rdata': continue
    col = p.u32(r)
    if col is None or p.sec(col) != '.rdata': continue
    if p.u32(col) != 0: continue
    tdp = p.u32(col + 12); chd = p.u32(col + 16)
    if not tdp or not chd or p.sec(tdp) != '.data' or p.sec(chd) != '.rdata': continue
    name = td(tdp)
    if not name or (p.cstr(tdp + 8, 256) or '')[:3] not in ('.?A',): continue
    # r is the meta pointer, r+4 the vftable
    vt = r + 4
    if (vt) not in p.relocset: continue
    funcs = []
    a = vt
    while a in p.relocset:
        f = p.u32(a)
        if not (t0 <= f < t1): break
        if a != vt and any(x == a for x in ()): break
        funcs.append(f); a += 4
        # stop at the next vtable's meta pointer
        nx = p.u32(a)
        if nx is not None and p.sec(nx) == '.rdata' and p.u32(nx) == 0 and p.u32(nx + 12) and p.sec(p.u32(nx + 12) or 0) == '.data':
            break
    off = p.u32(col + 4)
    nb = p.u32(chd + 8); bca = p.u32(chd + 12); attr = p.u32(chd + 4)
    bases = []
    for i in range(nb or 0):
        bcd = p.u32(bca + 4 * i)
        bt = td(p.u32(bcd)); ncont = p.u32(bcd + 4)
        mdisp, pdisp, vdisp, battr = struct.unpack('<iiiI', p.read(bcd + 8, 16))
        bases.append({'name': bt, 'contained': ncont, 'mdisp': mdisp, 'pdisp': pdisp, 'vdisp': vdisp})
    c = classes.setdefault(name, {'name': name, 'td': '%08X' % tdp, 'bases': bases, 'attr': attr, 'vtables': []})
    c['vtables'].append({'vt': '%08X' % vt, 'offset': off, 'funcs': ['%08X' % f for f in funcs]})
# classes known only from type descriptors (no vtable)
o = 0
for n, v, sz, ro, rs in p.secs:
    if n != '.data': continue
    blob = p.data[ro:ro + rs]
    for m in re.finditer(rb'\.\?A[VU][^\0]{1,200}@@\0', blob):
        va = v + m.start() - 8
        nm = demangle_td(m.group(0)[:-1].decode('latin1'))
        if nm not in classes: classes[nm] = {'name': nm, 'td': '%08X' % va, 'bases': [], 'attr': None, 'vtables': []}
json.dump(sorted(classes.values(), key=lambda c: c['name']), open(sys.argv[2], 'w'), indent=1)
print(len(classes), 'classes,', sum(len(c['vtables']) for c in classes.values()), 'vtables,',
      len(set(f for c in classes.values() for v in c['vtables'] for f in v['funcs'])), 'distinct virtual functions')
