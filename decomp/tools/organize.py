#!/usr/bin/env python3
"""Split exported decompilation (JSON lines from ExportDecomp.java) into per-unit .cpp files.
Units: classes/namespaces from symbol names, Lua library files, source files named in asserts; functions without
a label join the unit before them (MSVC keeps each object file's code together).
usage: organize.py DECOMP.jsonl SYMS.sym BINFEAT.json OUTDIR [--game NAME]"""
import sys, json, os, re, collections
dec = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8')]
syms = {}
for l in open(sys.argv[2], encoding='utf-8'):
    if l.startswith('#') or l.startswith('SLOT') or not l.strip(): continue
    q = l.split('#', 1); b = q[0].split(None, 2)
    syms[int(b[0], 16)] = (b[2].strip(), q[1].strip() if len(q) > 1 else '')
bf = {int(k, 16): v for k, v in json.load(open(sys.argv[3])).items()}
outdir = sys.argv[4]; game = sys.argv[sys.argv.index('--game') + 1] if '--game' in sys.argv else ''
def top_scope(name):
    depth = 0; parts = []; cur = ''
    i = 0
    while i < len(name):
        c = name[i]
        if c == '<': depth += 1
        elif c == '>': depth -= 1
        if depth == 0 and name.startswith('::', i): parts.append(cur); cur = ''; i += 2; continue
        cur += c; i += 1
    parts.append(cur)
    return parts[:-1]
def fname(s): return re.sub(r'[^A-Za-z0-9_.-]+', '_', s).strip('_')[:80]
items = []
for d in dec:
    a = int(d['a'], 16)
    nm, src = syms.get(a, (None, ''))
    label = None
    if nm:
        if src.startswith('lua-lib') or 'lua-lib' in src:
            m = re.search(r'\((\w+)\.c\)', src); label = 'lua/' + (m.group(1) if m else 'lua')
        else:
            sc = top_scope(nm)
            if sc:
                base = sc[0] if not sc[0].startswith('N') or len(sc) == 1 else '_'.join(sc)
                if sc[0].startswith('Lua_'): base = None
                elif '<' in base: base = 'templates/' + base.split('<')[0]
                label = base
    if not label and a in bf:
        for s in bf[a]['strings']:
            m = re.match(r'^(?:\.\\|e:\\prog\\att1\\|e:\\Prog\\ATThrone\\)(?:new\\|InctancedGrass\\)?([\w]+)\.(cpp|h)$', s, re.I)
            if m and m.group(2).lower() == 'cpp': label = 'src/' + m.group(1); break
    if not label and d['name'].startswith(('Unwind@', '__', '_', 'Catch@')) and int(d['a'], 16) > 0x5E0000:
        label = 'crt'
    items.append([a, label, d])
items.sort(key=lambda x: x[0])
prev = 'start'
for it in items:
    if it[1] is None: it[1] = prev if not prev.startswith('templates/') else 'misc_%06X' % (it[0] >> 12 << 12)
    else: prev = it[1]
units = collections.defaultdict(list)
for a, lab, d in items: units[lab].append((a, d))
os.makedirs(outdir, exist_ok=True)
index = []
for lab, fs in sorted(units.items(), key=lambda x: x[1][0][0]):
    path = os.path.join(outdir, fname(lab.replace('/', '__')) + '.cpp') if '/' not in lab else os.path.join(outdir, lab.split('/')[0], fname(lab.split('/', 1)[1]) + '.cpp')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('// %s: unit %s, %d functions, %08X..%08X\n// Raw Ghidra decompilation - generated, not compilable as is.\n\n' % (game, lab, len(fs), fs[0][0], fs[-1][0]))
        for a, d in fs:
            nm = syms.get(a, (d['name'], ''))
            f.write('// %08X  %s  [%s, %d bytes]%s\n' % (a, nm[0], d['cc'], d['size'], ('  (' + nm[1] + ')') if nm[1] else ''))
            f.write(d['c'].strip() + '\n\n')
    index.append((lab, len(fs), fs[0][0], fs[-1][0], os.path.relpath(path, outdir)))
with open(os.path.join(outdir, 'INDEX.tsv'), 'w') as f:
    for x in index: f.write('%s\t%d\t%08X\t%08X\t%s\n' % x)
print(len(units), 'units,', len(items), 'functions')
