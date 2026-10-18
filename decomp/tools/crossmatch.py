#!/usr/bin/env python3
"""Match functions between two builds of the engine (AttT -> Valkyrie).
Anchors: same-named RTTI classes (vtable slots), exports, masked-byte hashes, unique string sets;
then propagation through call lists and address order.  Output: TSV addrA addrB how.
usage: crossmatch.py A.exe A_feat.json A_rtti.json B.exe B_feat.json B_rtti.json OUT.tsv"""
import sys, json, hashlib, collections; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__))); from pe import PE
import capstone
A = PE(sys.argv[1]); FA = {int(k, 16): v for k, v in json.load(open(sys.argv[2])).items()}; RA = json.load(open(sys.argv[3]))
B = PE(sys.argv[4]); FB = {int(k, 16): v for k, v in json.load(open(sys.argv[5])).items()}; RB = json.load(open(sys.argv[6]))
out = sys.argv[7]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def mhash(p, a, f):
    code = p.read(a, f['size'])
    h = bytearray()
    for i in md.disasm(code, a):
        b = bytearray(i.bytes)
        if b[0] in (0xE8, 0xE9) and len(b) == 5: b[1:] = b'\0\0\0\0'
        for k in range(len(b) - 3):
            if i.address + k in p.relocset: b[k:k + 4] = b'\0\0\0\0'
        h += b
        if i.mnemonic == 'int3': break
    return hashlib.md5(h).hexdigest()
HA = {a: mhash(A, a, f) for a, f in FA.items()}
HB = {b: mhash(B, b, f) for b, f in FB.items()}
M = {}; R = {}; how = {}
def sizeok(a, b):
    sa, sb = FA[a]['size'], FB[b]['size']
    return HA[a] == HB[b] or (min(sa, sb) / max(sa, sb, 1) >= 0.7)
def match(a, b, w, check=True):
    if a in M or b in R or a not in FA or b not in FB: return False
    if check and not sizeok(a, b): return False
    M[a] = b; R[b] = a; how[a] = w; return True
# 1. RTTI vtables of same-named classes
vb = {}
for c in RB:
    for v in c['vtables']: vb[(c['name'], v['offset'])] = v['funcs']
for c in RA:
    for v in c['vtables']:
        fb = vb.get((c['name'], v['offset']))
        if not fb or len(fb) != len(v['funcs']): continue
        for x, y in zip(v['funcs'], fb): match(int(x, 16), int(y, 16), 'vtable', check=False)
# 2. exports
ea = {e.name: A.base + e.address for e in A.pe.DIRECTORY_ENTRY_EXPORT.symbols}
for e in B.pe.DIRECTORY_ENTRY_EXPORT.symbols:
    if e.name in ea: match(ea[e.name], B.base + e.address, 'export', check=False)
# 2b. Lua registration tables {"name", func} with the same names, Lunar method tables, Lua globals
def regtables(p):
    t0, t1 = p.text_range(); out = []
    for r in p.relocs:
        ents = []; va = r
        while va in p.relocset and va + 4 in p.relocset:
            n = p.cstr(p.u32(va), 40); f = p.u32(va + 4)
            if not n or not (t0 <= f < t1): break
            ents.append((n, f)); va += 8
        if len(ents) >= 2: out.append(ents)
    return out
tb = {tuple(n for n, f in e): e for e in regtables(B)}
for e in regtables(A):
    k = tuple(n for n, f in e)
    if k in tb:
        for (n, f), (n2, g) in zip(e, tb[k]): match(f, g, 'luatable', check=False)
import os
extra = os.environ.get('XMATCH_EXTRA')  # "A_lunar.json,B_lunar.json,A_globals.tsv,B_globals.tsv"
if extra:
    la, lb, ga, gb = extra.split(',')
    def lunar(fn): return {tuple(m[0] for m in t['methods']): [int(m[1], 16) for m in t['methods']] for t in json.load(open(fn))}
    xa, xb = lunar(la), lunar(lb)
    for k, fa in xa.items():
        if k in xb and len(k) >= 2:
            for f, g in zip(fa, xb[k]): match(f, g, 'lunar')
    def glob_(fn):
        d = collections.defaultdict(set)
        for l in open(fn):
            q = l.split('\t'); d[q[1]].add(int(q[0], 16))
        return d
    ya, yb = glob_(ga), glob_(gb)
    for n, s1 in ya.items():
        s2 = yb.get(n)
        if s2 and len(s1) == 1 and len(s2) == 1: match(next(iter(s1)), next(iter(s2)), 'luaglobal', check=False)
# 3. unique masked hashes (non-trivial size)
ca = collections.Counter(HA.values()); cb = collections.Counter(HB.values())
ib = {h: b for b, h in HB.items() if cb[h] == 1}
for a, h in HA.items():
    if ca[h] == 1 and h in ib and FA[a]['size'] >= 16: match(a, ib[h], 'bytes')
# 4. unique string sets
def skey(f): return tuple(sorted(set(f['strings']))) if len(set(f['strings'])) >= 1 and sum(len(s) for s in f['strings']) >= 6 else None
sa = collections.defaultdict(list); sb = collections.defaultdict(list)
for a, f in FA.items():
    k = skey(f)
    if k: sa[k].append(a)
for b, f in FB.items():
    k = skey(f)
    if k: sb[k].append(b)
for k, la in sa.items():
    lb = sb.get(k)
    if lb and len(la) == 1 and len(lb) == 1: match(la[0], lb[0], 'strings')
# 5. propagation
SA = sorted(FA); SB = sorted(FB)
ia = {a: i for i, a in enumerate(SA)}; ib2 = {b: i for i, b in enumerate(SB)}
changed = True; rounds = 0
while changed and rounds < 30:
    changed = False; rounds += 1
    for a, b in list(M.items()):
        ca_ = [c for c in dict.fromkeys(FA[a]['calls']) if isinstance(c, int) and c in FA]
        cb_ = [c for c in dict.fromkeys(FB[b]['calls']) if isinstance(c, int) and c in FB]
        anchors = [(i, cb_.index(M[c])) for i, c in enumerate(ca_) if c in M and M[c] in cb_]
        mono = all(y1 < y2 for (_, y1), (_, y2) in zip(anchors, anchors[1:]))
        if not mono: continue
        anchors = [(-1, -1)] + anchors + [(len(ca_), len(cb_))]
        for (i0, j0), (i1, j1) in zip(anchors, anchors[1:]):
            ua = [c for c in ca_[i0 + 1:i1] if c not in M]; ub = [c for c in cb_[j0 + 1:j1] if c not in R]
            if len(ua) == len(ub) and 0 < len(ua) <= 3:
                for x, y in zip(ua, ub):
                    if match(x, y, 'calls'): changed = True
    # address order: gaps between consecutive matches
    ms = sorted(M.items())
    for (a0, b0), (a1, b1) in zip(ms, ms[1:]):
        if b1 <= b0: continue
        ga = SA[ia[a0] + 1:ia[a1]]; gb = SB[ib2[b0] + 1:ib2[b1]]
        if ga and len(ga) == len(gb) and len(ga) <= 40:
            if all(x not in M for x in ga) and all(y not in R for y in gb):
                for x, y in zip(ga, gb):
                    if match(x, y, 'order'): changed = True
with open(out, 'w') as f:
    for a in sorted(M): f.write('%08X\t%08X\t%s\n' % (a, M[a], how[a]))
print('matched %d of %d (A) / %d (B):' % (len(M), len(FA), len(FB)), dict(collections.Counter(how.values())), 'rounds', rounds)
