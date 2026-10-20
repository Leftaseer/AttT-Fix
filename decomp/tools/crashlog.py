#!/usr/bin/env python3
"""Names the addresses of a crash in decomp_debug.log (a build made with -D DECOMP_DEBUG_LOG): the crash address
and the return addresses found on the stack, each as the function it is in: a replaced one (f_XXXXXXXX of the
generated code or a hand-written name, from the build's .map) or an original one (symbols/GAME.sym, else the
function start from symbols/GAME_functions.tsv).

usage: crashlog.py decomp_debug.log ATThrone.map symbols/GAME_functions.tsv [symbols/GAME.sym]"""
import bisect, re, sys

log, mapf, funcs = sys.argv[1:4]
starts, names = [], {}
for l in open(funcs):
    if l[0] != '#':
        q = l.split('\t')
        starts.append(int(q[0], 16))
starts.sort()
if len(sys.argv) > 4:
    for l in open(sys.argv[4], encoding='utf-8'):
        q = l.split('#')[0].split(None, 2)
        if len(q) == 3 and q[1] == 'f':
            names[int(q[0], 16)] = q[2].strip()
new = []            # (address, symbol) of the new code
for l in open(mapf, encoding='utf-8', errors='replace'):
    q = l.split()
    # symbols of the sections after the original ones (new code, its constants and the new import table)
    if len(q) >= 4 and re.match(r'^[0-9a-f]{16}$', q[2]) and int(q[2], 16) >= 0x8D2000 and \
            not q[1].startswith(('__real@', '__imp', '__xmm@', '??_C@')):
        new.append((int(q[2], 16), q[1]))
new.sort()
nkeys = [a for a, _ in new]


def name(a):
    if new and a >= new[0][0]:
        i = bisect.bisect_right(nkeys, a) - 1
        if i >= 0:
            return 'new code %s+%X' % (new[i][1], a - new[i][0])
    i = bisect.bisect_right(starts, a) - 1
    if i < 0:
        return '?'
    s = starts[i]
    return 'original %08X %s+%X' % (s, names.get(s, ''), a - s)


for l in open(log, encoding='utf-8', errors='replace'):
    l = l.rstrip('\n')
    print(l)
    m = re.match(r'crash \w+ at ([0-9A-F]{8})', l)
    if m:
        print('    at        %s' % name(int(m.group(1), 16)))
    if l.startswith('  stack:'):
        for v in l.split()[1:]:
            print('    called at %s  (%s)' % (v, name(int(v, 16))))
