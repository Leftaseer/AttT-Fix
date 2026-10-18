# Find luaL_Reg-like tables {const char* name; lua_CFunction f;} terminated by {0,0}.
import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__))); from pe import PE
p = PE(sys.argv[1]); t0, t1 = p.text_range()
rel = p.relocs; tabs = []
i = 0
while i < len(rel):
    va = rel[i]; ents = []
    while True:
        n = p.u32(va); f = p.u32(va + 4)
        if va in p.relocset and va + 4 in p.relocset and n and f and t0 <= f < t1 and p.sec(n) in ('.rdata', '.data'):
            s = p.cstr(n, 64)
            if s and s.replace('_', '').isalnum():
                ents.append((s, f)); va += 8; continue
        break
    if len(ents) >= 2 and p.u32(va) == 0:
        tabs.append((rel[i], ents)); i = rel.index(va) if va in p.relocset else i + 2 * len(ents)
    else: i += 1
for a, e in tabs:
    print('%08X %d %s' % (a, len(e), ' '.join('%s=%X' % x for x in e[:200])))
