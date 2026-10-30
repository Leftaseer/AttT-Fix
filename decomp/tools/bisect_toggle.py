#!/usr/bin/env python3
"""Find the replaced function behind a difference in a picture, with a build made with build.py --toggle (and
-D DECOMP_TEST_INPUT): the first k replaced functions (by address) on, the rest off (decomp_toggle.txt through
rungame.py's TOGGLE), binary search on k.  bad = TEST.sh's picture shots/bis_NAME_end.png differs from REF (a grey
thumbnail of CROP, RMSE > LIMIT); REF is the picture of a run with everything switched off.  The engine's own
functions stay on (they run the test input).  Found this way: 0x45E830 (trees at height 0), 0x4402A0 (walls).

usage: bisect_toggle.py NAME TEST.sh REF.png CROP LIMIT     (in /opt/re; BISECT_EXE: the toggle build, default
       rb/v68tg/ATThrone.exe; the log is out/bisect_NAME.log; TEST.sh takes the exe and GT_NAME, TOGGLE)
"""
import subprocess, os, sys
EXE = os.environ.get('BISECT_EXE', 'rb/v68tg/ATThrone.exe')
name, test, ref, crop, limit = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5])
os.chdir('/opt/re')
eng = ['00421220','0042E770','0042E930','0042EA90','0042EB70','0042EFF0','0042F100','0042F160','0042F640','00449E80',
       '00449F80','0044A9C0','0044BAB0','0044E480','0046CEB0','0046CEF0','0046CF30']
L = sorted(set(l.split()[0].upper().zfill(8) for l in open(os.path.join(os.path.dirname(EXE), 'work_attt', 'replace.txt')) if l.strip()))
L = [x for x in L if 0x420600 <= int(x, 16) < 0x607000 and x not in eng]
log = open('out/bisect_%s.log' % name, 'a')
def thumb(p):
    return "<(convert %s -crop %s -resize 100x88 -colorspace gray png:-)" % (p, crop)
def bad(k):
    tf = '/opt/re/toggle_%s.txt' % name
    with open(tf, 'w') as f:
        f.write('- 00420600-00607000\n')
        if k:
            f.write('+ %s-%s\n' % (L[0], L[k - 1]))
        for e in eng:
            f.write('+ %s\n' % e)
    env = dict(os.environ, TOGGLE=tf, GT_NAME='bis_' + name, NOCHECK='1')
    rc = subprocess.call(['bash', test, EXE], env=env)
    sh = 'shots/bis_%s_end.png' % name
    if rc != 0 or not os.path.exists(sh):
        r = 1.0
    else:
        o = subprocess.run("compare -metric RMSE %s %s null: 2>&1" % (thumb(sh), thumb(ref)), shell=True,
                           executable='/bin/bash', capture_output=True, text=True).stdout
        r = float(o.split('(')[1].split(')')[0])
        os.remove(sh)
    print('k=%d (%s) rc=%d rmse=%.3f' % (k, L[k - 1] if k else '-', rc, r), file=log, flush=True)
    return r > limit
lo, hi = 0, len(L)
print('N=%d' % len(L), file=log, flush=True)
while hi - lo > 1:
    mid = (lo + hi) // 2
    if bad(mid):
        hi = mid
    else:
        lo = mid
print('culprit %s (k=%d)' % (L[hi - 1], hi), file=log, flush=True)
