#!/usr/bin/env python3
"""The indirect calls whose pop is still unknown, for a build made with -D DECOMP_TRACE_ICALLS
(rebuild/src/engine/icalltrace.cpp): 'ADDRESS LENGTH' per line, for decomp_trace_sites.txt next to the exe.
Calls already measured (symbols/GAME_icall_pops.tsv) are left out.

usage: tracesites.py GAME.exe out/GAME_icalls.tsv symbols/GAME_icall_pops.tsv OUT.txt"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import PE
import capstone

pe = PE(sys.argv[1])
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
measured = {l.split()[0].upper() for l in open(sys.argv[3]) if l.strip() and l[0] != '#'}
out = []
for l in open(sys.argv[2]):
    if l[0] == '#':
        continue
    q = l.rstrip('\n').split('\t')
    if q[3] == '-1' and q[5] == '-1' and q[0] not in measured:     # no cleanup after it, pop unknown
        a = int(q[0], 16)
        i = next(md.disasm(pe.read(a, 16), a, 1))
        if i.mnemonic == 'call':
            out.append('%08X %d' % (a, i.size))
open(sys.argv[4], 'w').write('\n'.join(out) + '\n')
print('%d call sites' % len(out))
