#!/usr/bin/env python3
"""Print decompiled functions from an ExportDecomp JSON-lines file.
usage: show.py DECOMP.jsonl ADDR|NAME-REGEX [...] [--callers] """
import sys, json, re
dec = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8')]
by_a = {int(d['a'], 16): d for d in dec}
for q in sys.argv[2:]:
    if q.startswith('--'): continue
    try:
        hits = [by_a[int(q, 16)]]
    except (ValueError, KeyError):
        hits = [d for d in dec if re.search(q, d['ns'] + '::' + d['name'])]
    for d in hits:
        print('// ===== %s  %s::%s  [%s, %d bytes]' % (d['a'].upper(), d['ns'], d['name'], d['cc'], d['size']))
        print(d['c'].strip()); print()
