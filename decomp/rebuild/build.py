#!/usr/bin/env python3
"""Rebuild ATThrone.exe from the original exe plus the decompiled sources in rebuild/src.

    python3 build.py --exe PATH/ATThrone.exe [--out build/ATThrone.exe] [--laa]

1. The original exe is converted into a relinkable object (tools/exe2obj.py); nothing of the game is stored in
   this repository, the user's own exe is the input.
2. rebuild/src/**/*.c|cpp is compiled with clang for i686-pc-windows-msvc (the MSVC ABI of the original).
3. Every function preceded by DECOMP(<AttT address>) replaces the original: a jmp is placed at the old entry
   and every pointer to it (vtables, tables) is redirected.  An adapter is generated when the original used an
   /LTCG register convention or kept volatile registers its callers rely on.
4. sub_XXXXXXXX / d_XXXXXXXX names used by the sources are defined at the original functions and globals
   (cdecl shims for register conventions).
5. lld-link puts everything together; tools/verify_relink.py checks the untouched original bytes.
Addresses in the sources are AttT ones; for Valkyrie they are translated through symbols/attt2valk*.tsv.
"""
import argparse, os, re, struct, subprocess, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOLS = os.path.join(ROOT, 'tools')
SYMS = os.path.join(ROOT, 'symbols')
sys.path.insert(0, TOOLS)
from pe import PE  # noqa: E402

GAMES = {0x475EABAF: 'attt', 0x4883FB4F: 'valk'}
REG_ORDER = ['ECX', 'EAX', 'EDX', 'EBX', 'ESI', 'EDI']


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.stderr.write('$ %s\n%s%s' % (' '.join(cmd), r.stdout, r.stderr))
        sys.exit(1)
    return r.stdout


def load_functions(game):
    """addr -> (size, regs_in, retpop, clobber)"""
    f = {}
    for l in open(os.path.join(SYMS, '%s_functions.tsv' % game)):
        if l.startswith('#'):
            continue
        a, size, regs, retpop, clob = l.rstrip('\n').split('\t')[:5]
        f[int(a, 16)] = (int(size), [r for r in regs.split(',') if r and r != 'EBP'],
                         int(retpop or 0), set(x for x in clob.split(',') if x))
    return f


def load_map(name):
    m = {}
    path = os.path.join(SYMS, name)
    if os.path.exists(path):
        for l in open(path):
            if l.startswith('#') or not l.strip():
                continue
            p = l.split('\t')
            m[int(p[0], 16)] = int(p[1], 16)
    return m


def split_params(text):
    """'(lua_State *L, int narg)' -> number of parameters"""
    t = text.strip()
    if t.startswith('('):
        t = t[1:t.rfind(')')]
    t = t.strip()
    if t in ('', 'void'):
        return 0
    depth = 0
    n = 1
    for c in t:
        if c in '(<[':
            depth += 1
        elif c in ')>]':
            depth -= 1
        elif c == ',' and depth == 0:
            n += 1
    return n


def scan_sources(files):
    """DECOMP annotations: (attt_addr, qualified name, param count, is_member) and ORIG_FN prototypes."""
    decomp, protos = [], {}
    for fn in files:
        src = open(fn, encoding='utf-8').read()
        src_nc = re.sub(r'/\*.*?\*/|//[^\n]*', lambda m: ' ' * len(m.group(0)), src, flags=re.S)
        for m in re.finditer(r'DECOMP\(\s*([0-9A-Fa-f]{8})\s*\)\s*([^{;]*?)\b([A-Za-z_][\w:~<>]*)\s*(\((?:[^()]|\([^()]*\))*\))', src_nc):
            addr, ret, name, params = int(m.group(1), 16), m.group(2), m.group(3), m.group(4)
            decomp.append((addr, name, split_params(params), '::' in name, fn))
        for m in re.finditer(r'ORIG_(FN|STDCALL|FASTCALL|THISCALL)\(\s*([0-9A-Fa-f]{8})\s*,[^,]*,\s*(\((?:[^()]|\([^()]*\))*\))\s*\)', src_nc):
            protos[int(m.group(2), 16)] = (m.group(1), split_params(m.group(3)))
    return decomp, protos


def nm_symbols(obj):
    out = run(['llvm-nm', obj])
    defined, undefined = [], []
    for l in out.splitlines():
        p = l.split()
        if len(p) == 2 and p[0] == 'U':
            undefined.append(p[1])
        elif len(p) == 3 and p[1] in 'TtDdBbRr':
            defined.append(p[2])
    return defined, undefined


def demangle(sym):
    if not sym.startswith('?'):
        return sym.lstrip('_@').split('@')[0]
    out = subprocess.run(['llvm-undname'], input=sym + '\n', capture_output=True, text=True).stdout.strip().splitlines()
    d = out[-1] if out else sym
    m = re.search(r'([\w:~<>]+)\(', d)
    return m.group(1) if m else d


def symbol_conv(sym, member):
    if member or re.search(r'@@[A-Z][A-D]E', sym):
        return 'thiscall'
    if sym.startswith('@'):
        return 'fastcall'
    if re.match(r'^_\w+@\d+$', sym):
        return 'stdcall'
    return 'cdecl'


def adapter_asm(name, target, conv, regs, nstack, retpop, preserve):
    """Entry used by original callers.  conv 'cdecl': target(regs..., stack args...), caller pops;
    conv 'thiscall': ECX passes through, target pops the stack args.  Volatile registers in preserve are kept."""
    a = ['\t.globl\t%s' % name, '%s:' % name]
    saved = [r for r in ('EAX', 'ECX', 'EDX') if r in preserve]
    for r in saved:
        a.append('\tpushl\t%%%s' % r.lower())
    off = 4 * len(saved) + 4 + 4 * (nstack - 1)
    for i in range(nstack):
        a.append('\tpushl\t%d(%%esp)' % off)
    if conv == 'cdecl':
        for r in reversed(regs):
            a.append('\tpushl\t%%%s' % r.lower())
    a.append('\tcalll\t%s' % target)
    if conv == 'cdecl' and nstack + len(regs):
        a.append('\taddl\t$%d, %%esp' % (4 * (nstack + len(regs))))
    for r in reversed(saved):
        a.append('\tpopl\t%%%s' % r.lower())
    a.append('\tretl\t$%d' % retpop if retpop else '\tretl')
    return a


def shim_asm(name, raw, regs, nstack, retpop):
    """cdecl name(regs..., stack args...) -> original raw entry with its register convention."""
    a = ['\t.globl\t%s' % name, '%s:' % name, '\tpushl\t%ebx', '\tpushl\t%esi', '\tpushl\t%edi', '\tpushl\t%ebp']
    nr = len(regs)
    # after the 4 pushes the first argument is at 20(%esp)
    for i in reversed(range(nstack)):
        a.append('\tpushl\t%d(%%esp)' % (20 + 4 * (nr + i) + 4 * (nstack - 1 - i)))
    for j, r in enumerate(regs):
        a.append('\tmovl\t%d(%%esp), %%%s' % (20 + 4 * nstack + 4 * j, r.lower()))
    a.append('\tcalll\t%s' % raw)
    if not retpop and nstack:
        a.append('\taddl\t$%d, %%esp' % (4 * nstack))
    a += ['\tpopl\t%ebp', '\tpopl\t%edi', '\tpopl\t%esi', '\tpopl\t%ebx', '\tretl']
    return a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--exe', required=True)
    ap.add_argument('--out', default=os.path.join(HERE, 'build', 'ATThrone.exe'))
    ap.add_argument('--laa', action='store_true', help='mark the result Large Address Aware')
    ap.add_argument('--only', help='comma-separated source files (default: all of rebuild/src)')
    a = ap.parse_args()

    pe = PE(a.exe)
    game = GAMES.get(pe.pe.FILE_HEADER.TimeDateStamp)
    if not game:
        sys.exit('unknown exe (TimeDateStamp %08X)' % pe.pe.FILE_HEADER.TimeDateStamp)
    work = os.path.join(os.path.dirname(os.path.abspath(a.out)), 'work_' + game)
    os.makedirs(work, exist_ok=True)
    funcs = load_functions(game)
    fmap = load_map('attt2valk.tsv') if game == 'valk' else None
    dmap = load_map('attt2valk_data.tsv') if game == 'valk' else None

    def gaddr(x, data=False):
        if game == 'attt':
            return x
        m = (dmap if data else fmap) or {}
        if x not in m:
            sys.exit('no Valkyrie address for AttT %08X; add it to symbols/attt2valk%s.tsv' % (x, '_data' if data else ''))
        return m[x]

    files = sorted(glob.glob(os.path.join(HERE, 'src', '**', '*.c'), recursive=True) +
                   glob.glob(os.path.join(HERE, 'src', '**', '*.cpp'), recursive=True))
    if a.only:
        files = [f for f in files if os.path.basename(f) in a.only.split(',')]
    decomp, protos = scan_sources(files)

    # compile
    objs = []
    cflags = ['--target=i686-pc-windows-msvc', '-O2', '-march=pentium4', '-msse2', '-fms-extensions',
              '-fno-builtin', '-ffreestanding', '-fno-stack-protector', '-I', os.path.join(HERE, 'include'),
              '-I', os.path.join(HERE, 'src'), '-D', 'DECOMP_GAME_%s=1' % game.upper()]
    for fn in files:
        obj = os.path.join(work, os.path.relpath(fn, os.path.join(HERE, 'src')).replace(os.sep, '_') + '.obj')
        extra = ['-std=c++17', '-fno-exceptions', '-fno-rtti'] if fn.endswith('.cpp') else ['-std=c11']
        run(['clang'] + cflags + extra + ['-c', fn, '-o', obj])
        objs.append(obj)
    rt = os.path.join(work, 'rt_support.obj')
    run(['clang'] + cflags + ['-c', os.path.join(HERE, 'rt_support.c'), '-o', rt])
    objs.append(rt)

    defined, undefined = set(), set()
    for o in objs:
        d, u = nm_symbols(o)
        defined |= set(d)
        undefined |= set(u)
    undefined -= defined

    syms, repl, asm = [], [], ['\t.text']
    # replacements
    by_name = {}
    for s in defined:
        by_name.setdefault(demangle(s), []).append(s)
    for addr, name, nparams, member, fn in decomp:
        cands = by_name.get(name) or by_name.get(name.split('::')[-1]) or []
        cands = [c for c in cands if not c.startswith('_sub_') and not c.startswith('raw_')]
        if len(cands) != 1:
            sys.exit('%s: cannot find the compiled symbol of %s (candidates: %s)' % (fn, name, cands))
        sym = cands[0]
        ga = gaddr(addr)
        size, regs, retpop, clob = funcs.get(ga, (0, [], 0, {'EAX', 'ECX', 'EDX'}))
        preserve = {'EAX', 'ECX', 'EDX'} - clob - set(regs)
        conv = symbol_conv(sym, member)
        if conv == 'thiscall':
            nstack = nparams
            direct = set(regs) <= {'ECX'} and retpop == 4 * nstack
        elif conv == 'cdecl':
            nstack = nparams - len(regs)
            direct = not regs and retpop == 0
        else:
            nstack = nparams
            direct = (conv == 'stdcall' and not regs and retpop == 4 * nstack) or \
                     (conv == 'fastcall' and set(regs) <= {'ECX', 'EDX'} and retpop == 4 * max(0, nstack - 2))
        if direct and not preserve:
            repl.append((ga, sym))
            continue
        if conv not in ('cdecl', 'thiscall') or (conv == 'thiscall' and not set(regs) <= {'ECX'}):
            sys.exit('%s: %s: original %08X takes %s and pops %d bytes; write the replacement as a cdecl function '
                     'with the register parameters first (%s)' % (fn, name, ga, ','.join(regs) or 'no registers',
                                                                   retpop, ', '.join(REG_ORDER)))
        ad = 'adp_%08X' % addr
        asm += adapter_asm(ad, sym, conv, regs if conv == 'cdecl' else [], max(nstack, 0), retpop, preserve)
        repl.append((ga, ad))
    # references to originals
    for s in sorted(undefined):
        m = re.match(r'^[_@]?(sub|d)_([0-9A-Fa-f]{8})(@\d+)?$', s)
        if not m:
            continue
        kind, addr = m.group(1), int(m.group(2), 16)
        if kind == 'd':
            syms.append((gaddr(addr, True), s))
            continue
        ga = gaddr(addr)
        size, regs, retpop, clob = funcs.get(ga, (0, [], 0, set()))
        conv, nparams = protos.get(addr, ('FN', None))
        if conv == 'FN' and regs:
            if nparams is None:
                sys.exit('sub_%08X has a register convention: declare it with ORIG_FN' % addr)
            raw = 'raw_%08X' % addr
            syms.append((ga, raw))
            asm += shim_asm(s, '_' + raw, regs, nparams - len(regs), retpop)
        else:
            syms.append((ga, s if s[0] in '?@' else s[1:] if s.startswith('_') else s))
    # exe2obj takes C names without the leading underscore (it adds it unless the name starts with ? or @)
    with open(os.path.join(work, 'syms.txt'), 'w') as f:
        for ga, s in syms:
            f.write('%08X %s\n' % (ga, s))
    with open(os.path.join(work, 'replace.txt'), 'w') as f:
        for ga, s in repl:
            f.write('%08X %s\n' % (ga, s[1:] if s.startswith('_') else s))
    if len(asm) > 1:
        gs = os.path.join(work, 'glue.s')
        open(gs, 'w').write('\n'.join(asm) + '\n')
        go = os.path.join(work, 'glue.obj')
        run(['clang', '--target=i686-pc-windows-msvc', '-c', gs, '-o', go])
        objs.append(go)

    run([sys.executable, '-I', os.path.join(TOOLS, 'exe2obj.py'), a.exe, work,
         '--syms', os.path.join(work, 'syms.txt'), '--replace', os.path.join(work, 'replace.txt')])
    # imports the new code needs and the original exe does not use
    have = {}
    for d in glob.glob(os.path.join(work, 'imports', '*.def')):
        for l in open(d).read().splitlines()[2:]:
            have[l.split('==')[0].strip()] = d
    extra_map = {}
    ef = os.path.join(HERE, 'imports_extra.txt')
    if os.path.exists(ef):
        for l in open(ef):
            q = l.split('#')[0].split()
            if len(q) == 2:
                extra_map[q[0]] = q[1]
    add = {}
    for s_ in sorted(undefined):
        if not s_.startswith('__imp_'):
            continue
        n = s_[6:]
        if not n.startswith('?'):
            n = n[1:]                      # C names carry the extra underscore
        if n in have:
            continue
        dll = extra_map.get(n) or ('MSVCP80.dll' if 'std@@' in n else None)
        if not dll:
            sys.exit('new code imports %s: add "%s <dll>" to rebuild/imports_extra.txt' % (n, n))
        add.setdefault(dll, []).append(n)
    for dll, names in add.items():
        d = os.path.join(work, 'imports', dll.lower().replace('.dll', '') + '.def')
        if not os.path.exists(d):
            open(d, 'w').write('LIBRARY %s\nEXPORTS\n' % dll)
        with open(d, 'a') as f:
            for n in names:
                f.write('  %s == %s\n' % (n, n))
    libs = []
    for d in glob.glob(os.path.join(work, 'imports', '*.def')):
        lib = d[:-4] + '.lib'
        run(['llvm-dlltool', '-m', 'i386', '-d', d, '-l', lib])
        libs.append(lib)
    # new code and data go into .ntext/.nrdata/.ndata/.nbss and the import tables into .zidata, all placed after
    # the original sections, which keep their original addresses (AttTFix and other tools use absolute addresses)
    run([sys.executable, '-I', os.path.join(TOOLS, 'coffrename.py')] + objs)
    rsp = open(os.path.join(work, 'link.rsp')).read().split()
    rsp += ['/merge:.idata=.zidata', '/merge:.didat=.zidata']
    if a.laa:
        rsp.append('/largeaddressaware')
    mapf = os.path.splitext(a.out)[0] + '.map'
    out = run(['lld-link'] + rsp + ['/out:' + a.out, '/map:' + mapf, os.path.join(work, 'orig.obj')] + objs +
              [os.path.join(work, 'resources.res')] + libs)
    # same TimeDateStamp as the original, so tools that recognise the game by it (AttTFix) keep working
    import pefile
    npe = pefile.PE(a.out)
    for s_ in pe.pe.sections:
        n_ = s_.Name.rstrip(b'\0')
        for t_ in npe.sections:
            if t_.Name.rstrip(b'\0') == n_ and n_ in (b'.text', b'.rdata', b'.data') and t_.VirtualAddress != s_.VirtualAddress:
                sys.exit('original section %s moved: %08X -> %08X' % (n_.decode(), s_.VirtualAddress, t_.VirtualAddress))
    npe.FILE_HEADER.TimeDateStamp = pe.pe.FILE_HEADER.TimeDateStamp
    npe.OPTIONAL_HEADER.CheckSum = npe.generate_checksum()
    data = npe.write()
    npe.close()
    open(a.out, 'wb').write(data)
    print(run([sys.executable, '-I', os.path.join(TOOLS, 'verify_relink.py'), a.exe, a.out, mapf,
               '--replace', os.path.join(work, 'replace.txt')]).strip())
    print('%s: %d replaced functions, %d original symbols used -> %s' % (game, len(repl), len(syms), a.out))


if __name__ == '__main__':
    main()
