#!/usr/bin/env python3
"""Which replaced functions a coverage build (build.py --coverage) ran.

The build's decomp_coverage.bin files (one dword per marked point: an address just inside a function of the new
code) are joined and every point is mapped to the function that holds it through the build's .map: f_XXXXXXXX
(hand-written in src/fixed or generated) and the engine's own C++ functions.

usage: coverage.py BUILD.map COV.bin [COV.bin ...] [--fixed DIR] [--names attt.sym] [--out PREFIX]
  prints the totals; with --out writes PREFIX_run.tsv and PREFIX_notrun.tsv (address, kind, name)
"""
import argparse
import bisect
import os
import re
import struct


def read_map(path):
    """(address, symbol) of the code of the new objects (not orig.obj), sorted"""
    syms = []
    for line in open(path, errors='replace'):
        m = re.match(r'\s*[0-9a-f]{4}:[0-9a-f]{8}\s+(\S+)\s+([0-9a-f]{8,16})\s+(?:f\s+)?(\S+)\s*$', line)
        if not m or m.group(3) == 'orig.obj':
            continue
        syms.append((int(m.group(2), 16), m.group(1), m.group(3)))
    syms.sort()
    return syms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('map')
    ap.add_argument('bins', nargs='+')
    ap.add_argument('--fixed', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rebuild',
                                                    'src', 'fixed'))
    ap.add_argument('--names', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'symbols',
                                                    'attt.sym'))
    ap.add_argument('--out')
    a = ap.parse_args()

    syms = read_map(a.map)
    addrs = [s[0] for s in syms]
    hit = set()
    for b in a.bins:
        data = open(b, 'rb').read()
        for (p,) in struct.iter_unpack('<I', data[:len(data) // 4 * 4]):
            i = bisect.bisect_right(addrs, p) - 1
            if i >= 0 and p - addrs[i] < 256:    # (the hook is called in the prologue)
                hit.add(syms[i][1])

    fixed = set(int(f[2:10], 16) for f in os.listdir(a.fixed) if re.match(r'f_[0-9A-F]{8}\.c$', f))
    names = {}
    if os.path.exists(a.names):
        for line in open(a.names, errors='replace'):
            p = line.split()
            if len(p) >= 3 and p[1] == 'f':
                names.setdefault(int(p[0], 16), ' '.join(p[2:]).split(' #')[0])
    funcs = {}                      # name in the map -> (original address or None, kind)
    for ad, name, obj in syms:
        m = re.match(r'[_@]f_([0-9A-F]{8})(?:@\d+)?$', name)
        if m:
            o = int(m.group(1), 16)
            funcs[name] = (o, 'hand' if o in fixed and obj.startswith('auto_f_') else 'auto')
        elif obj.startswith('engine_') and name.startswith('?'):
            funcs[name] = (None, 'engine')
    tot = {}
    for name, (o, kind) in funcs.items():
        t = tot.setdefault(kind, [0, 0])
        t[0] += 1
        t[1] += name in hit
    for kind in ('hand', 'auto', 'engine'):
        if kind in tot:
            n, h = tot[kind]
            print('%-7s %5d of %5d run (%.1f%%)' % (kind, h, n, 100.0 * h / max(n, 1)))
    n = sum(t[0] for t in tot.values())
    h = sum(t[1] for t in tot.values())
    print('all     %5d of %5d run (%.1f%%)' % (h, n, 100.0 * h / max(n, 1)))
    if a.out:
        for suffix, want in (('run', True), ('notrun', False)):
            with open('%s_%s.tsv' % (a.out, suffix), 'w') as f:
                for name, (o, kind) in sorted(funcs.items(), key=lambda x: (x[1][0] or 0, x[0])):
                    if (name in hit) == want:
                        f.write('%s\t%s\t%s\n' % ('%08X' % o if o else '-', kind,
                                                  names.get(o, '') if o else name))


if __name__ == '__main__':
    main()
