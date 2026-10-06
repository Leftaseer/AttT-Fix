# compact summary of AttTFix_perf.log (both current and .prev): FPS per scene and the latest counters
import re, sys, os
d = sys.argv[1] if len(sys.argv) > 1 else '.'
for f in ('AttTFix_perf.prev.log', 'AttTFix_perf.log'):
    p = os.path.join(d, f)
    if not os.path.exists(p): continue
    L = open(p, encoding='utf-8', errors='replace').read().splitlines()
    print('==', f)
    st = [l for l in L if ' STATS ' in l]
    for l in st[-6:]:
        m = re.search(r'fps=([\d.]+).*?avg=([\d.]+).*?u\.scene\[(\w+)\]=([\d.]+).*?r\.scene\[\w+\]=([\d.]+)', l)
        if m: print('  %s fps %s frame %sms upd %s render %s' % (m.group(3), m.group(1), m.group(2), m.group(4), m.group(5)))
    for k in ('RENDEROPT', 'TREESORT', 'SKIN fast', 'BILLBOARDS', 'EFFECTS lazy', 'Begin callers', 'SOUND', 'ANIM mesh', 'PARTICLES', 'last period modules', 'last period self', 'last period AttTFix'):
        x = [l for l in L if k in l]
        if x: print('  ' + x[-1][15:15 + 260])
