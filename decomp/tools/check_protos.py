#!/usr/bin/env python3
"""Check the sub_XXXXXXXX declarations of the hand files (rebuild/src/fixed) against the register conventions of
auto/<game>/convs.tsv.  build.py keeps one prototype per original address and a hand file's wins over the generated
code's, so a hand file that declares a callee taking EAX/EBX/... as plain __thiscall rewires every generated call to
it (the register arguments then come from nowhere).  Such callees must be declared __cdecl with the register
parameters first, in the order of convs.tsv (self, eax, ...).

Every source of rebuild/src (the engine's C++ ORIG_* declarations too, under any #ifdef) is checked the same way,
and an address declared with two conventions is reported: whichever declaration the build sees first wins.

usage: check_protos.py [auto folder, default /opt/re/auto/attt_v67]   (exit 1 when something is wrong)
"""
import glob
import os
import re
import sys

auto = sys.argv[1] if len(sys.argv) > 1 else '/opt/re/auto/attt_v67'
fixed = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rebuild', 'src', 'fixed')
conv = {}
for line in open(os.path.join(auto, 'convs.tsv')):
    p = line.rstrip('\n').split('\t')
    if len(p) >= 3 and not p[0].startswith('#'):
        conv[int(p[0], 16)] = ([r for r in p[1].split(',') if r], int(p[2] or 0))
bad = 0
srcdir = os.path.dirname(fixed)
files = sorted(glob.glob(os.path.join(srcdir, '**', '*.c'), recursive=True) +
               glob.glob(os.path.join(srcdir, '**', '*.cpp'), recursive=True))
macro = {'ORIG_FN': '__cdecl', 'ORIG_STDCALL': '__stdcall', 'ORIG_FASTCALL': '__fastcall', 'ORIG_THISCALL': '__thiscall'}
seen = {}
for f in files:
    src = open(f, encoding='utf-8', errors='replace').read()
    decls = [(m.group(1), m.group(2)) for m in
             re.finditer(r'(__cdecl|__stdcall|__fastcall|__thiscall)\s+sub_([0-9A-Fa-f]{8})\s*\(', src)]
    decls += [(macro[m.group(1)], m.group(2)) for m in
              re.finditer(r'\b(ORIG_FN|ORIG_STDCALL|ORIG_FASTCALL|ORIG_THISCALL)\(\s*([0-9A-Fa-f]{8})\s*,', src)]
    for c, a_ in decls:
        a = int(a_, 16)
        first = seen.setdefault(a, (c, f))
        if first[0] != c:
            print('%s: sub_%08X is %s but %s declares it %s' % (os.path.relpath(f, srcdir), a, c,
                                                               os.path.relpath(first[1], srcdir), first[0]))
            bad += 1
        if a not in conv:
            continue
        regs, pop = conv[a]
        if c == '__thiscall' and (not regs or regs[0] != 'ECX' or len(regs) > 1):
            print('%s: sub_%08X is __thiscall but takes %s' % (os.path.basename(f), a, ','.join(regs) or 'no registers'))
            bad += 1
        elif c == '__stdcall' and regs:
            print('%s: sub_%08X is __stdcall but takes %s' % (os.path.basename(f), a, ','.join(regs)))
            bad += 1
        elif c == '__cdecl' and pop and not regs:
            print('%s: sub_%08X is __cdecl but pops %d bytes' % (os.path.basename(f), a, pop))
            bad += 1
sys.exit(1 if bad else 0)
