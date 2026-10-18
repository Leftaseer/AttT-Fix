#!/usr/bin/env python3
"""Match functions of a statically linked C library (source features from srcfeat.py) to a binary
(features from binfeat.py).  Seeds: luaL_Reg-style tables {"name", func} in source and binary,
explicit seeds, unique strings; then propagation through call lists and source order.
usage: libmatch.py SRCFEAT.json SRCDIR BINFEAT.json EXE OUT.tsv [seed=ADDR:name ...] [range=LO:HI]"""
import sys, json, re, os, glob, collections
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__))); from pe import PE
src = json.load(open(sys.argv[1])); srcdir = sys.argv[2]; bf = json.load(open(sys.argv[3])); p = PE(sys.argv[4]); outp = sys.argv[5]
seeds = {}; lo, hi = 0, 1 << 32
for a in sys.argv[6:]:
    if a.startswith('seed='):
        ad, nm = a[5:].split(':'); seeds[nm] = int(ad, 16)
    if a.startswith('range='):
        l, h = a[6:].split(':'); lo, hi = int(l, 16), int(h, 16)
bins = {int(k, 16): v for k, v in bf.items() if lo <= int(k, 16) < hi}
baddrs = sorted(bins)
sname = {f['name']: f for f in src}
# drop duplicate static names (keep first) but remember file order
order = collections.defaultdict(list)
for i, f in enumerate(src): order[f['file']].append(f['name'])
M = {}; R = {}  # src name -> bin addr, bin addr -> src name
forbid = set()
def match(n, a, why):
    if n in M or a in R or n not in sname or a not in bins or (n, a) in forbid: return False
    if why in ('call', 'order') and not consistent(n, a): forbid.add((n, a)); return False
    M[n] = a; R[a] = n; why_[n] = why; return True
why_ = {}
for n, a in seeds.items(): match(n, a, 'seed')
def big(strs): return set(x for x in strs if len(x) >= 3)
def expanded_calls(n, depth=2):
    out = set(); todo = [(n, 0)]
    while todo:
        x, d = todo.pop()
        for c in sname[x]['calls'] if x in sname else []:
            if c not in out:
                out.add(c)
                if d + 1 < depth and c in sname: todo.append((c, d + 1))
    return out
def consistent(n, a):
    ss, bs = big(sname[n]['strings']), big(bins[a]['strings'])
    if ss or bs:
        if not ss or not bs: return False
        if len(ss & bs) / len(ss | bs) < 0.5: return False
    bc = set(R[c] for c in bins[a]['calls'] if isinstance(c, int) and c in R)
    if bc:
        ex = expanded_calls(n)
        if len(bc & ex) / len(bc) < 0.75: return False
    sc = set(c for c in sname[n]['calls'] if c in M)
    if sc:
        bcalls = set(c for c in bins[a]['calls'] if isinstance(c, int))
        hit = sum(1 for c in sc if M[c] in bcalls)
        if hit / len(sc) < 0.5 and len(sc) >= 2: return False
    return True
# 1. registration tables in source: {"name", func}
regs = []  # list of lists of (luaname, cname)
for fn in glob.glob(os.path.join(srcdir, '*.c')):
    t = open(fn, encoding='latin1').read()
    for m in re.finditer(r'static const (?:luaL_Reg|struct luaL_reg) \w+\[\] = \{(.*?)\};', t, re.S):
        ents = re.findall(r'\{"(\w+)",\s*(\w+)\}', m.group(1))
        if ents: regs.append(ents)
# binary tables: name list -> funcs
def bin_tables():
    out = []
    rel = p.relocs; i = 0
    t0, t1 = p.text_range()
    for r in rel:
        ents = []; va = r
        while va in p.relocset and va + 4 in p.relocset:
            n = p.cstr(p.u32(va), 40); f = p.u32(va + 4)
            if not n or not (t0 <= f < t1): break
            ents.append((n, f)); va += 8
        if len(ents) >= 2: out.append(ents)
    return out
bt = bin_tables()
for ents in regs:
    names = [e[0] for e in ents]
    for b in bt:
        if [x[0] for x in b] == names:
            for (ln, cn), (_, f) in zip(ents, b): match(cn, f, 'table')
            break
# 2. unique strings
def sset(strs): return set(s for s in strs if len(s) >= 4)
sidx = collections.defaultdict(set); bidx = collections.defaultdict(set)
for f in src:
    for s in sset(f['strings']): sidx[s].add(f['name'])
for a in baddrs:
    for s in sset(bins[a]['strings']): bidx[s].add(a)
changed = True; rounds = 0
while changed:
    changed = False; rounds += 1
    for n, a in list(M.items()):
        if why_[n] in ('call', 'order') and not consistent(n, a):
            del M[n]; del R[a]; forbid.add((n, a)); changed = True
    for s, ns in sidx.items():
        if len(ns) == 1 and len(bidx.get(s, ())) == 1:
            if match(next(iter(ns)), next(iter(bidx[s])), 'string'): changed = True
    # 3. call-list propagation
    for n, a in list(M.items()):
        sc = [c for c in dict.fromkeys(sname[n]['calls']) if c in sname]
        bc = [c for c in dict.fromkeys(bins[a]['calls']) if isinstance(c, int) and c in bins]
        # anchors
        anchors = [(i, bc.index(M[c])) for i, c in enumerate(sc) if c in M and M[c] in bc]
        anchors = [(-1, -1)] + anchors + [(len(sc), len(bc))]
        for (i0, j0), (i1, j1) in zip(anchors, anchors[1:]):
            us = [c for c in sc[i0 + 1:i1] if c not in M]
            ub = [c for c in bc[j0 + 1:j1] if c not in R]
            if len(us) == len(ub) == 1:
                if match(us[0], ub[0], 'call'): changed = True
    # 4. order inside a file: unmatched gaps of equal size between matched neighbours
    for fl, names in order.items():
        idx = [(i, M[n]) for i, n in enumerate(names) if n in M]
        for (i0, a0), (i1, a1) in zip(idx, idx[1:]):
            if a1 <= a0: continue
            us = [n for n in names[i0 + 1:i1] if n not in M]
            ub = [b for b in baddrs if a0 < b < a1 and b not in R]
            if us and len(us) == len(ub) and why_[names[i0]] != 'order' and why_[names[i1]] != 'order':
                for n, b in zip(us, ub):
                    if match(n, b, 'order'): changed = True
with open(outp, 'w') as f:
    for n, a in sorted(M.items(), key=lambda x: x[1]): f.write('%08X\t%s\t%s\t%s\n' % (a, n, sname[n]['file'], why_[n]))
cnt = collections.Counter(why_.values())
print('matched %d of %d source functions (%s), rounds %d' % (len(M), len(sname), dict(cnt), rounds))
per = collections.Counter(sname[n]['file'] for n in M); tot = collections.Counter(f['file'] for f in src)
print(' '.join('%s:%d/%d' % (k, per[k], tot[k]) for k in sorted(tot)))
