# usage: strref.py exe "string" -> code locations whose relocated imm32 points to the string
import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__))); from pe import PE
p = PE(sys.argv[1]); needle = sys.argv[2].encode('cp1251') + b'\0'
o = 0; hits = []
while True:
    o = p.data.find(needle, o)
    if o < 0: break
    for n, v, sz, ro, rs in p.secs:
        if ro <= o < ro + rs and (o == 0 or p.data[o-1] == 0): hits.append(v + o - ro)
    o += 1
for h in hits:
    refs = [r for r in p.relocs if p.u32(r) == h]
    print('%08X' % h, ' '.join('%08X(%s)' % (r, p.sec(r)) for r in refs))
