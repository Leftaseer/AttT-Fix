#!/usr/bin/env python3
"""Find the auto-decompiled functions that change the behaviour of the game: build with the first N functions of
the sorted list and run a test, binary search for the first one that breaks it, put it on the bad list, repeat
until everything left passes.  Each round costs about log2(N) builds and test runs.

    autobisect.py ORIG.exe AUTO_DIR WORK [--test 'COMMAND {exe}']

The default test is tools/winetest.sh (the start-up path without game data).  A test command gets the rebuilt exe
in place of {exe} and passes with exit status 0, e.g. a tools/rungame.py run checked by a script.
Bad functions are appended to WORK/bad.txt (one address per line), the log is WORK/bisect.log; give bad.txt to
the next autodecomp/build run as an exclusion, or fix the cause."""
import argparse, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('orig'); ap.add_argument('auto'); ap.add_argument('work')
ap.add_argument('--test')
ap.add_argument('-D', dest='defines', action='append', default=[], help='define for build.py (e.g. DECOMP_TEST_INPUT)')
ap.add_argument('--base', help='functions known to be good (one address per line): always built in, not searched')
ap.add_argument('--range', help='LO,HI: resume a search known to pass with LO functions and fail with HI')
a = ap.parse_args()
os.makedirs(a.work, exist_ok=True)
allf = sorted(l.split('\t')[0] for l in open(os.path.join(a.auto, 'functions.tsv')) if l.split('\t')[1] == 'compiled')
base = [l.strip() for l in open(a.base) if l.strip()] if a.base else []
allf = [x for x in allf if x not in set(base)]
badf = os.path.join(a.work, 'bad.txt')
bad = set(l.strip() for l in open(badf)) if os.path.exists(badf) else set()
log = open(os.path.join(a.work, 'bisect.log'), 'a')
exe = os.path.join(a.work, 'bis', 'ATThrone.exe')


def test(lst):
    lp = os.path.join(a.work, 'bisect_list.txt')
    open(lp, 'w').write('\n'.join(base + lst) + '\n')
    r = subprocess.run([sys.executable, os.path.join(HERE, '..', 'rebuild', 'build.py'), '--exe', a.orig, '--out', exe,
                        '--auto', a.auto, '--auto-list', lp] + sum((['-D', d] for d in a.defines), []), capture_output=True, text=True)
    if r.returncode:
        log.write('build failed: %s\n' % r.stderr[-800:]); log.flush()
        sys.exit('build failed')
    if a.test:
        ok = subprocess.run(a.test.replace('{exe}', exe), shell=True, capture_output=True).returncode == 0
    else:
        r = subprocess.run(['bash', os.path.join(HERE, 'winetest.sh'), a.orig, exe, os.path.join(a.work, 'wt')],
                           capture_output=True, text=True)
        ok = 'same behaviour' in r.stdout
    log.write('%d functions: %s\n' % (len(lst), 'ok' if ok else 'DIFF')); log.flush()
    return ok


resume = [int(x) for x in a.range.split(',')] if a.range else None
while True:
    cand = [x for x in allf if x not in bad]
    if resume:
        lo, hi = resume
        resume = None
    else:
        if test(cand):
            log.write('all remaining pass\n'); log.flush()
            break
        lo, hi = 0, len(cand)      # the prefix of length lo passes, of length hi fails
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if test(cand[:mid]):
            lo = mid
        else:
            hi = mid
    culprit = cand[hi - 1]
    log.write('BAD %s\n' % culprit); log.flush()
    print('bad:', culprit, flush=True)
    bad.add(culprit)
    open(badf, 'a').write(culprit + '\n')
