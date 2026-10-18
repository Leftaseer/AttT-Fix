#!/usr/bin/env python3
"""Map data addresses between two builds through matched functions with the same instruction layout:
each relocated operand at the same offset votes for (address in A -> address in B).
usage: datamap.py A.exe A_feat.json B.exe B_feat.json FUNCMAP.tsv OUT.tsv"""
import sys, os, json, collections; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from pe import PE
A = PE(sys.argv[1]); FA = {int(k, 16): v for k, v in json.load(open(sys.argv[2])).items()}
B = PE(sys.argv[3]); FB = {int(k, 16): v for k, v in json.load(open(sys.argv[4])).items()}
fm = [(int(a, 16), int(b, 16)) for a, b, w in (l.split('\t') for l in open(sys.argv[5]))]
votes = collections.defaultdict(collections.Counter)
textA = A.text_range(); textB = B.text_range()
for a, b in fm:
    sa, sb = FA[a]['size'], FB[b]['size']
    if sa != sb: continue
    ra = [r - a for r in A.relocs if a <= r < a + sa] if False else None
    ca, cb = A.read(a, sa), B.read(b, sb)
    # relocation offsets inside the function
    import bisect
    i0 = bisect.bisect_left(A.relocs, a); i1 = bisect.bisect_left(A.relocs, a + sa)
    j0 = bisect.bisect_left(B.relocs, b); j1 = bisect.bisect_left(B.relocs, b + sb)
    oa = [r - a for r in A.relocs[i0:i1]]; ob = [r - b for r in B.relocs[j0:j1]]
    if oa != ob: continue
    for o in oa:
        x, y = A.u32(a + o), B.u32(b + o)
        if x is None or y is None: continue
        if textA[0] <= x < textA[1]: continue   # code pointers are covered by the function map
        votes[x][y] += 1
out = 0
with open(sys.argv[6], 'w') as f:
    f.write('# AttT data address\tValkyrie data address\tvotes\n')
    for x in sorted(votes):
        (y, n), = votes[x].most_common(1)
        tot = sum(votes[x].values())
        if n * 2 > tot:
            f.write('%08X\t%08X\t%d\n' % (x, y, n)); out += 1
print(out, 'data addresses mapped')
