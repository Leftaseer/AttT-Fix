#!/usr/bin/env python3
"""Translate a symbol file from AttT addresses to Valkyrie through the function cross-match (and the AttTFix
exeaddr.h table for data).  usage: portsyms.py IN.sym attt2valk.tsv exeaddr.h OUT.sym"""
import sys, re
fm = {int(a, 16): int(b, 16) for a, b, w in (l.split('\t') for l in open(sys.argv[2]))}
txt = open(sys.argv[3]).read().split('g_valkEnFix')[0]
dm = {int(o, 16): int(v, 16) for o, v in re.findall(r'\{ 0x([0-9A-F]+), 0x([0-9A-F]+) \}', txt)}
n = miss = 0
with open(sys.argv[4], 'w') as f:
    for l in open(sys.argv[1], encoding='utf-8'):
        if l.startswith('#') or not l.strip(): continue
        if l.startswith('SLOT'): f.write(l); continue
        q = l.split('#', 1); b = q[0].split(None, 2)
        if len(b) < 3: continue
        a = int(b[0], 16)
        t = fm.get(a) if b[1] == 'f' else dm.get(a)
        if t is None: t = dm.get(a)
        if t is None: miss += 1; continue
        f.write('%08X %s %s # %s\n' % (t, b[1], b[2].strip(), (q[1].strip() if len(q) > 1 else '')))
        n += 1
print('ported', n, 'missing', miss)
