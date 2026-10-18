#!/usr/bin/env python3
"""Check that a relinked exe contains the original sections unchanged apart from relocated pointers.
usage: verify_relink.py ORIG.exe NEW.exe NEW.map [--replace FILE]"""
import sys, struct, re, pefile
orig, new, mapf = sys.argv[1:4]
repl = set()
if '--replace' in sys.argv:
    for l in open(sys.argv[sys.argv.index('--replace') + 1]):
        p = l.split('#')[0].split()
        if p: repl.add(int(p[0], 16))
po, pn = pefile.PE(orig), pefile.PE(new)
bo, bn = po.OPTIONAL_HEADER.ImageBase, pn.OPTIONAL_HEADER.ImageBase
starts = {}
for l in open(mapf):
    m = re.search(r'__orig_(\w+)_start\s+([0-9a-fA-F]+)', l)
    if m: starts['.' + m.group(1)] = int(m.group(2), 16)
def img(pe):
    return pe.get_memory_mapped_image()
mo, mn = img(po), img(pn)
def imports(pe):
    d = {}
    for e in pe.DIRECTORY_ENTRY_IMPORT:
        for i in e.imports: d[i.address] = (e.dll.decode().lower(), i.name or i.ordinal)
    return d
io, inn = imports(po), imports(pn)
osecs = [(s.Name.rstrip(b'\0').decode(), bo + s.VirtualAddress, s.Misc_VirtualSize) for s in po.sections]
def omap(va):
    for n, v, sz in osecs:
        if n in starts and v <= va <= v + sz: return starts[n] + va - v
    if bo <= va < osecs[0][1]: return bn + va - bo
relocs = set(bo + e.rva for b in po.DIRECTORY_ENTRY_BASERELOC for e in b.entries if e.type == 3)
bad = 0; checked = 0; nrel = 0
for n, v, sz in osecs:
    if n not in starts: continue
    ns = starts[n]
    a = v; end = v + sz
    while a < end:
        if a in relocs and a + 4 <= end:
            to = struct.unpack_from('<I', mo, a - bo)[0]
            tn = struct.unpack_from('<I', mn, ns + a - v - bn)[0]
            nrel += 1
            if to in io:
                ok = inn.get(tn) == io[to]
            elif to in repl: ok = True
            else:
                ok = omap(to) == tn
            if not ok:
                bad += 1
                if bad < 20: print('reloc mismatch at %08X: orig %08X new %08X' % (a, to, tn))
            a += 4; continue
        if any(r <= a < r + 5 for r in repl if r <= a < r + 5):
            a += 1; continue
        if mo[a - bo] != mn[ns + a - v - bn]:
            bad += 1
            if bad < 20: print('byte mismatch at %08X' % a)
        checked += 1; a += 1
print('sections %s, %d bytes and %d pointers checked, %d mismatches' % (','.join(starts), checked, nrel, bad))
sys.exit(1 if bad else 0)
