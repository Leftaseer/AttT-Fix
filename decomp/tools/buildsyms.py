#!/usr/bin/env python3
"""Merge all name sources into one symbol file (ADDRESS KIND NAME # source).
Priority: manual > exports > RTTI destructors > Lua tables/globals > Lua library > RTTI generic slots.
Slot propagation: a manual/export name for virtual slot N of class C names every override of that slot in
classes derived from C.
usage: buildsyms.py --exe EXE --rtti RTTI.json --rttisym RTTI.sym --lunar LUNAR.json --luaglobals G.tsv
                    --lualib LIB.tsv --manual M.sym [--manual ...] --out OUT.sym"""
import sys, json, argparse, subprocess, re, collections
ap = argparse.ArgumentParser()
for k in ('exe', 'rtti', 'rttisym', 'lunar', 'luaglobals', 'lualib', 'out'): ap.add_argument('--' + k)
ap.add_argument('--manual', action='append', default=[])
ap.add_argument('--ported', action='append', default=[])
a = ap.parse_args()
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__))); from pe import PE
p = PE(a.exe)
S = {}  # addr -> (kind, name, src, prio)
def put(addr, kind, name, src, prio):
    if addr in S and S[addr][3] >= prio: return
    S[addr] = (kind, name, src, prio)
slotdefs = []
def readsym(fn):
    for l in open(fn, encoding='utf-8'):
        if l.startswith('SLOT '):
            q = l.split('#')[0].split(); slotdefs.append((q[1], int(q[2]), q[3])); continue
        c = l.split('#', 1); body = c[0].split(None, 2)
        if len(body) == 3: yield int(body[0], 16), body[1], body[2].strip(), (c[1].strip() if len(c) > 1 else '')
# RTTI
for ad, k, n, c in readsym(a.rttisym):
    pr = 30 if c.startswith('rtti-d') or 'vftable' in n else 10
    put(ad, k, n, c or 'rtti', pr)
# exports (demangled)
for e in p.pe.DIRECTORY_ENTRY_EXPORT.symbols:
    dm = subprocess.run(['llvm-undname'], input=e.name.decode() + '\n', capture_output=True, text=True).stdout.strip().splitlines()[-1]
    m = re.search(r'(?:__thiscall|__cdecl|__stdcall) ([\w:<>~]+)\(', dm)
    if m: put(p.base + e.address, 'f', m.group(1), 'export', 90)
# Lua method tables
if a.lunar:
    for t in json.load(open(a.lunar)):
        for nm, f in t['methods']:
            put(int(f, 16), 'f', 'Lua_%s::%s' % (t['table'], nm), 'lua-method', 40)
if a.luaglobals:
    for l in open(a.luaglobals):
        f, nm, idx, at = l.rstrip('\n').split('\t')
        put(int(f, 16), 'f', 'LuaGlobal_%s' % nm, 'lua-global', 45)
if a.lualib:
    for l in open(a.lualib):
        f, nm, fl, why = l.rstrip('\n').split('\t')
        if why in ('seed', 'table', 'string'): put(int(f, 16), 'f', nm, 'lua-lib(%s.c)' % fl, 50)
for fn in a.ported:
    for ad, k, n, c in readsym(fn): put(ad, k, n, 'ported:' + c.split(' ')[0] if c else 'ported', 70)
for fn in a.manual:
    for ad, k, n, c in readsym(fn): put(ad, k, n, 'manual', 100)
# tiny functions are folded by the linker and shared by unrelated classes (ret stubs, _purecall thunks):
# name them by what they do, above everything else
import capstone
_md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def stub_name(ad):
    code = p.read(ad, 16) or b''
    ins = []
    for i in _md.disasm(code, ad):
        ins.append(i)
        if i.mnemonic in ('ret', 'jmp') or len(ins) > 3: break
    if not ins or ins[-1].mnemonic not in ('ret', 'jmp'): return None
    if ins[-1].mnemonic == 'jmp':
        o = ins[0]
        if len(ins) == 1 and o.op_str.startswith('dword ptr ['):
            v = int(o.op_str[11:-1], 16) if o.op_str[11:-1].startswith('0x') else None
            if v in p.imports: return 'j_' + p.imports[v][1]
        return None
    body = ' '.join((i.mnemonic + ' ' + i.op_str).strip() for i in ins)
    names = {'ret': 'nullsub', 'ret 4': 'nullsub_4', 'ret 8': 'nullsub_8', 'ret 0xc': 'nullsub_12',
             'xor eax, eax ret': 'return0', 'xor eax, eax ret 4': 'return0_4', 'xor al, al ret': 'returnfalse',
             'xor al, al ret 4': 'returnfalse_4', 'mov al, 1 ret': 'returntrue', 'mov al, 1 ret 4': 'returntrue_4',
             'mov eax, 1 ret': 'return1', 'mov eax, ecx ret': 'returnthis', 'fldz ret': 'return0f'}
    return names.get(body)
fslot_all = set()
for c in json.load(open(a.rtti)):
    for v in c['vtables']:
        for f in v['funcs']: fslot_all.add(int(f, 16))
for ad in list(fslot_all) + [x for x, v in S.items() if v[0] == 'f']:
    n = stub_name(ad)
    if n: S[ad] = ('f', n, 'stub', 110)
# slot propagation
C = json.load(open(a.rtti))
bases = {c['name']: set(b['name'] for b in c['bases']) for c in C}
slots = collections.defaultdict(list)  # (class, off, slot) -> func
fslot = collections.defaultdict(list)
for c in C:
    for v in c['vtables']:
        for i, f in enumerate(v['funcs']):
            fslot[int(f, 16)].append((c['name'], v['offset'], i))
named = {}  # (ownerclass, off, slot) -> method name
for ad, (k, n, src, pr) in S.items():
    if pr < 90 or ad not in fslot or '::' not in n: continue
    cls, meth = n.rsplit('::', 1)
    for (c, off, i) in fslot[ad]:
        if c == cls: named[(c, off, i)] = meth
prop = 0
vt0 = {c['name']: [int(f, 16) for f in v['funcs']] for c in C for v in c['vtables'] if v['offset'] == 0}
rootnamed = {}
for (cls, off, i), meth in named.items():
    if off != 0: continue
    cands = [b for b in bases.get(cls, ()) | {cls} if b in vt0 and len(vt0[b]) > i]
    if not cands: continue
    root = min(cands, key=lambda b: len(bases.get(b, ())))
    rootnamed[(root, i)] = meth
for c_, i_, m_ in slotdefs: rootnamed[(c_, i_)] = m_
for (root, i), meth in rootnamed.items():
    for d, fl in vt0.items():
        if (root in bases.get(d, ()) or d == root) and len(fl) > i:
            ad = fl[i]; cur = S.get(ad)
            if cur and cur[3] >= 60: continue
            owner = cur[1].rsplit('::', 1)[0] if cur and '::' in cur[1] else d
            put(ad, 'f', '%s::%s' % (owner, meth), 'slot(%s)' % root, 60); prop += 1
with open(a.out, 'w', encoding='utf-8') as f:
    f.write('# Generated by buildsyms.py - do not edit; put hand-made names into *_manual.sym\n')
    for ad in sorted(S):
        k, n, src, pr = S[ad]; f.write('%08X %s %s # %s\n' % (ad, k, n, src))
print(len(S), 'symbols', dict(collections.Counter(v[2].split('(')[0] for v in S.values())), 'slot-propagated', prop)
