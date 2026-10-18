#!/usr/bin/env python3
"""Turn Ghidra's decompilation (ghidra/AutoExport.java) into C files that build.py can compile and link.

Every function whose decompiled text has no constructs that cannot be compiled faithfully (indirect calls with
unknown conventions, registers the decompiler could not attribute, SEH frames, bad instructions, ...) becomes
    DECOMP(XXXXXXXX) RET CC f_XXXXXXXX(PARAMS) { ... }
with its callees declared as sub_XXXXXXXX and its globals as G_XXXXXXXX over the original data (d_XXXXXXXX).
Each function is compiled on its own first; the ones that compile are grouped into translation units.
The result is raw decompiler output - correct only as far as Ghidra is - so tools/difftest.py --auto checks
every function against the original in the emulator before it is trusted.

usage: autodecomp.py AUTO.jsonl TYPES.h OUTDIR [--game attt] [--max N] [--jobs N]
Output (OUTDIR, keep it out of the public repository: it is the game's code): auto_pre.h, auto_NNN.c,
functions.tsv (address, status, reason)."""
import argparse, json, os, re, subprocess, sys, glob, hashlib
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
REBUILD = os.path.join(HERE, '..', 'rebuild')

BLOCK = [
    (r'\bunaff_\w+', 'unaffected register'), (r'\bextraout_\w+', 'extra output register'),
    (r'\bin_stack_\w+', 'stack outside the frame'), (r'\bin_[A-Z]{2,4}\b', 'register input'),
(r'WARNING: (?!Globals starting|Removing unreachable|Load size|Type propagation)', 'decompiler warning'),
    (r'UNRESOLVED', 'unresolved name'), (r'halt_baddata|halt_unimplemented|software_\w+\(|swi\(', 'bad instruction'),
    (r'\bLOCK\(\)|\bUNLOCK\(\)', 'locked instruction'), (r'_vbase_destructor|__alloca_probe', 'compiler helper'),
    (r'\bin_FS_OFFSET\b', 'TEB access'), (r'\bxRam|\bunique0x', 'unmapped storage'),
    (r'\.\.\.\)', 'varargs'), (r'\bCONCAT\d{3,}|\bSUB\d{3,}', 'wide value'),
]


def load_protos(path):
    p, imports = {}, set()
    for l in open(path, encoding='utf-8'):
        q = l.rstrip('\n').split('\t')
        if len(q) < 6:
            continue
        a, cc, custom, ret, params, varargs = q[:6]
        plist = [x.rsplit(' ', 1) for x in params.split(',') if x.strip()] if params else []
        p[int(a, 16)] = (cc, custom == 'true', ret, plist, varargs == 'true')
        if len(q) > 6 and q[6] == 'import':
            imports.add(int(a, 16))
    return p, imports


def has_indirect_call(code):
    """a call through a computed pointer: '(*...)(' or '(**...)(' with the parentheses balanced"""
    for m in re.finditer(r'\(\*', code):
        depth = 0
        i = m.start()
        while i < len(code):
            if code[i] == '(':
                depth += 1
            elif code[i] == ')':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        j = i + 1
        while j < len(code) and code[j] in ' \n':
            j += 1
        if j < len(code) and code[j] == '(':
            return True
    return False


def cc_word(cc, custom):
    if custom:
        return '__cdecl'
    return {'__thiscall': '__thiscall', '__fastcall': '__fastcall', '__stdcall': '__stdcall', '__cdecl': '__cdecl'}.get(cc)


def proto_text(name, pr):
    cc, custom, ret, plist, va = pr
    w = cc_word(cc, custom)
    if w is None:
        return None
    ps = []
    for i, (t, n) in enumerate(plist):
        ps.append('%s p%d' % (t, i))
    if va:
        ps.append('...')
    return '%s %s %s(%s)' % (ret, w, name, ', '.join(ps) if ps else 'void')


def body_of(code):
    i = code.find('{')
    if i < 0:
        return None
    return code[i:]


symaddr = {}
symname = {}
rets = {}


def convert(f, protos, skip, imports, impnames):
    a = int(f['a'], 16)
    if a in skip:
        return None, 'hand-decompiled'
    code = f['code']
    for pat, why in BLOCK:
        if re.search(pat, code):
            return None, why
    if has_indirect_call(code):
        return None, 'indirect call'
    pr = protos.get(a)
    if not pr:
        return None, 'no prototype'
    head = proto_text('f_%08X' % a, pr)
    if head is None:
        return None, 'unknown calling convention'
    body = body_of(code)
    if body is None:
        return None, 'no body'
    # parameter names of the definition: the decompiler's names
    names = re.match(r'[^(]*\((.*?)\)\s*\{', code.replace('\n', ' '), re.S)
    params = []
    if names:
        raw = names.group(1).strip()
        if raw and raw != 'void':
            params = [x.strip() for x in raw.split(',')]
    cc, custom, ret, plist, va = pr
    if va:
        return None, 'varargs'
    if len(params) != len(plist):
        return None, 'parameter count differs from the prototype'
    if ret.startswith('undefined') and not re.search(r'\breturn\s+[^;\s]', body):
        ret = 'void'               # the decompiler guessed a result that the function never sets
    rets[a] = ret
    head = '%s %s f_%08X(%s)' % (ret, cc_word(cc, custom), a, ', '.join(params) if params else 'void')
    # namespace prefixes the decompiler printed before calls (templates included)
    body = re.sub(r'(?:\b[A-Za-z_]\w*(?:<[^;{}()]*?>)?\s*::\s*)+(?=sub_[0-9A-F]{8})', '', body)
    # the SEH frame of C++ functions (fs:[0], printed as a global at FFDFF000): our frame layout differs, so the
    # registration is dropped; an exception then passes through without running this function's destructors
    body = re.sub(r'\n[^\n;]*\bG_FFDFF000\b[^\n;]*;', '\n', body)
    # vftable of the function's own class
    own = symname.get(a, '')
    if '::' in own:
        cls = own.rsplit('::', 1)[0]
        body = re.sub(r'(?<![\w:])vftable\b', cls + '::vftable', body)
    # addresses printed as symbol names
    def addr_ref(m):
        return '((void *)d_%s)' % m.group(2).upper()
    extra = set()
    def sym_ref(m):
        q = m.group(0).lstrip('&').replace(' ', '')
        ad = symaddr.get(q)
        if ad is None:
            raise KeyError(q)
        extra.add('%08X' % ad)
        return '((void *)d_%08X)' % ad
    body = re.sub(r'&?\b(LAB|PTR_LAB|PTR_FUN|PTR_DAT|PTR_s|FUN|s_\w+?|u_\w+?)_([0-9a-fA-F]{8})\b', addr_ref, body)
    if re.search(r'(?<![\w.>])(DAT_|PTR_|BYTE_|WORD_|DWORD_|UNK_)[0-9a-fA-F]{8}\b', body):
        return None, 'global of unknown type'
    try:
        body = re.sub(r'&?(?:\b[A-Za-z_][\w<>,]*(?:<[^;{}()]*?>)?::)+(?:vftable(?:_\w+)?|vbtable\w*|`[^`]*\'|\w+_meta_ptr)', sym_ref, body)
    except KeyError as e:
        return None, 'unknown symbol %s' % e
    for g in re.findall(r'\bG_([0-9A-F]{8})\b', body):
        ad = int(g, 16)
        if not (0x400000 <= ad < 0x1000000):
            return None, 'segment or out-of-image global'
    for x in re.findall(r'\(\(void \*\)d_([0-9A-F]{8})\)', body):
        extra.add(x)
    if '::' in body:
        return None, 'C++ name left'

    decls = []
    for c in f['callees']:
        ca = int(c, 16)
        cp = protos.get(ca)
        if not cp:
            return None, 'callee %s without prototype' % c
        if ca in imports:
            if ca not in impnames:
                return None, 'import %s not in the import table' % c
            cc, custom, ret, plist, va = cp
            w = cc_word(cc, False) or '__cdecl'
            ps = ', '.join(t for t, n in plist) if plist else 'void'
            if va:
                ps += ', ...'
            decls.append('DECOMP_C %s (%s *imp_%s)(%s) __asm__("%s");' % (ret, w, c, ps, impnames[ca]))
            decls.append('#define sub_%s (*imp_%s)' % (c, c))
            continue
        t = proto_text('sub_%s' % c, cp)
        if t is None:
            return None, 'callee %s with unknown calling convention' % c
        decls.append('DECOMP_C %s;' % t)
    for g, info in f['globals'].items():
        parts = info.split('|')
        decls.append('DECOMP_C char d_%s[];' % g)
        if parts[0] == 'code':
            decls.append('#define G_%s d_%s' % (g, g))
        elif parts[0] == 'ARRAY':
            decls.append('#define G_%s ((%s *)d_%s)' % (g, parts[1], g))
        else:
            decls.append('#define G_%s (*(%s *)d_%s)' % (g, parts[0], g))
    for s in f['strings']:
        decls.append('DECOMP_C char d_%s[];' % s)
        decls.append('#define S_%s d_%s' % (s, s))
    for x in sorted(extra):
        decls.append('DECOMP_C char d_%s[];' % x)
    # macros of this function only (the same global can have another type in another function)
    macros = [d for d in decls if d.startswith('#define')]
    decls = [d for d in decls if not d.startswith('#define')]
    undefs = ['#undef ' + d.split()[1] for d in macros]
    text = '/* @func %08X%s */\n%s\nDECOMP(%08X)\n%s\n%s\n%s\n' % (a, ' custom' if custom else '', '\n'.join(macros), a, head, body.strip(), '\n'.join(undefs))
    return (a, decls, text), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('jsonl'); ap.add_argument('types'); ap.add_argument('outdir')
    ap.add_argument('--exe', required=True, help='the original exe (import names)')
    ap.add_argument('--syms', action='append', default=[], help='symbols.tsv of Ghidra (DumpInfo) or .sym files')
    ap.add_argument('--max', type=int, default=0)
    ap.add_argument('--jobs', type=int, default=os.cpu_count() or 4)
    ap.add_argument('--per-unit', type=int, default=150)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    protos, imports = load_protos(a.jsonl + '.protos')
    for fn in a.syms:
        for l in open(fn, encoding='utf-8'):
            if l.startswith('#') or not l.strip():
                continue
            if '\t' in l:
                q = l.rstrip('\n').split('\t')
                try:
                    symaddr.setdefault(q[1].replace(' ', ''), int(q[0], 16))
                except ValueError:
                    pass
            else:
                q = l.split('#')[0].split(None, 2)
                if len(q) == 3:
                    symaddr.setdefault(q[2].strip().replace(' ', ''), int(q[0], 16))
                    if q[1] == 'f':
                        symname[int(q[0], 16)] = q[2].strip()
    sys.path.insert(0, HERE)
    from pe import PE
    pe = PE(a.exe)
    impnames = {}
    for addr, (dll, name) in pe.imports.items():
        impnames[addr] = ('__imp_' + name) if name.startswith('?') else ('__imp__' + name)
    # functions already written by hand
    skip = set()
    for fn in glob.glob(os.path.join(REBUILD, 'src', '**', '*.c*'), recursive=True):
        for m in re.finditer(r'DECOMP\(\s*([0-9A-Fa-f]{8})\s*\)', open(fn, encoding='utf-8').read()):
            skip.add(int(m.group(1), 16))
    pre = os.path.join(a.outdir, 'auto_pre.h')
    types = open(a.types, encoding='utf-8').read()
    # Ghidra's own names for a few base types
    types = types.replace('float10 ', 'double ')
    with open(pre, 'w', encoding='utf-8') as f:
        f.write('/* generated by tools/autodecomp.py */\n#pragma once\n#include "ghidra_prelude.h"\n')
        f.write(types)
    inc = ['-I', os.path.abspath(os.path.join(REBUILD, 'include')), '-I', os.path.abspath(a.outdir)]
    cflags = ['--target=i686-pc-windows-msvc', '-x', 'c', '-std=gnu11', '-fms-extensions', '-ffreestanding',
              '-fno-builtin', '-w', '-Wno-error=int-conversion', '-Wno-error=incompatible-pointer-types',
              '-Wno-error=incompatible-function-pointer-types', '-Wno-error=int-to-pointer-cast',
              '-Wno-error=return-type'] + inc
    pch = pre + '.pch'
    r = subprocess.run(['clang'] + cflags[:1] + ['-x', 'c-header', '-std=gnu11', '-fms-extensions', '-ffreestanding',
                        '-w'] + inc + [pre, '-o', pch], capture_output=True, text=True)
    if r.returncode:
        sys.stderr.write(r.stderr[:4000]); sys.exit('the types header does not compile')
    funcs = [json.loads(l) for l in open(a.jsonl, encoding='utf-8')]
    if a.max:
        funcs = funcs[:a.max]
    status = {}
    cands = []
    for f in funcs:
        res, why = convert(f, protos, skip, imports, impnames)
        if res is None:
            status[f['a']] = ('rejected', why)
        else:
            cands.append(res)
    tmp = os.path.join(a.outdir, 'tmp')
    os.makedirs(tmp, exist_ok=True)

    def check(c):
        addr, decls, text = c
        src = os.path.join(tmp, 'f_%08X.c' % addr)
        open(src, 'w', encoding='utf-8').write('#include "auto_pre.h"\n' + '\n'.join(decls) + '\n' + text)
        r = subprocess.run(['clang'] + cflags + ['-include-pch', pch, '-fsyntax-only', src], capture_output=True, text=True)
        os.remove(src)
        if r.returncode:
            err = next((l for l in r.stderr.splitlines() if 'error' in l), 'error')
            return addr, err.split('error:')[-1].strip()[:120]
        return addr, None
    ok = []
    with ThreadPoolExecutor(a.jobs) as ex:
        for (addr, err), c in zip(ex.map(check, cands), cands):
            if err:
                status['%08X' % addr] = ('compile error', err)
            else:
                ok.append(c)
                status['%08X' % addr] = ('compiled', '')
    for old in glob.glob(os.path.join(a.outdir, 'auto_*.c')):
        os.remove(old)
    ok.sort()
    n = 0
    for i in range(0, len(ok), a.per_unit):
        group = ok[i:i + a.per_unit]
        decls = []
        seen = set()
        for _, d, _ in group:
            for x in d:
                if x not in seen:
                    seen.add(x); decls.append(x)
        with open(os.path.join(a.outdir, 'auto_%03d.c' % n), 'w', encoding='utf-8') as f:
            f.write('/* generated by tools/autodecomp.py from Ghidra output - not reviewed */\n#include "auto_pre.h"\n')
            f.write('\n'.join(decls) + '\n\n')
            f.write('\n'.join(t for _, _, t in group))
        n += 1
    import shutil
    shutil.copy(a.jsonl + '.protos', os.path.join(a.outdir, 'protos'))
    with open(os.path.join(a.outdir, 'rets.tsv'), 'w') as f:
        for k in sorted(rets):
            f.write('%08X\t%s\n' % (k, rets[k]))
    with open(os.path.join(a.outdir, 'functions.tsv'), 'w') as f:
        for k in sorted(status):
            f.write('%s\t%s\t%s\n' % (k, status[k][0], status[k][1]))
    import collections
    c = collections.Counter(v[0] for v in status.values())
    print('functions: %s; %d units' % (dict(c), n))
    rc = collections.Counter(v[1] for v in status.values() if v[0] != 'compiled')
    for k, v in rc.most_common(15):
        print('  %5d %s' % (v, k))


if __name__ == '__main__':
    main()
