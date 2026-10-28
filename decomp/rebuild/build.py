#!/usr/bin/env python3
"""Rebuild ATThrone.exe from the original exe plus the decompiled sources in rebuild/src.

    python3 build.py --exe PATH/ATThrone.exe [--out build/ATThrone.exe] [--laa]

1. The original exe is converted into a relinkable object (tools/exe2obj.py); nothing of the game is stored in
   this repository, the user's own exe is the input.
2. rebuild/src/**/*.c|cpp is compiled with clang for i686-pc-windows-msvc (the MSVC ABI of the original).
3. Every function preceded by DECOMP(<AttT address>) replaces the original: a jmp is placed at the old entry;
   pointers to it (vtables, tables, addresses in code) keep the old address, so it has one address everywhere.  An adapter is generated when the original used an
   /LTCG register convention or kept volatile registers its callers rely on.
4. sub_XXXXXXXX / d_XXXXXXXX names used by the sources are defined at the original functions and globals
   (cdecl shims for register conventions).
5. lld-link puts everything together; tools/verify_relink.py checks the untouched original bytes.
Addresses in the sources are AttT ones; for Valkyrie they are translated through symbols/attt2valk*.tsv.
"""
import argparse, os, re, struct, subprocess, sys, glob, hashlib, json, shutil, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOLS = os.path.join(ROOT, 'tools')
SYMS = os.path.join(ROOT, 'symbols')
sys.path.insert(0, TOOLS)
from pe import PE  # noqa: E402

GAMES = {0x475EABAF: 'attt', 0x4883FB4F: 'valk'}
REG_ORDER = ['ECX', 'EAX', 'EDX', 'EBX', 'ESI', 'EDI']


def run(cmd, **kw):
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if os.environ.get('DECOMP_BUILD_TIMES') and time.time() - t0 > 1:
        sys.stderr.write('%5.1f s  %s\n' % (time.time() - t0, ' '.join(cmd)[:150]))
    if r.returncode != 0:
        sys.stderr.write('$ %s\n%s%s' % (' '.join(cmd), r.stdout, r.stderr))
        sys.exit(1)
    return r.stdout


# Compiler runs are cached (DECOMP_BUILD_CACHE, default ~/.cache/decomp_build): the key is the command, the source
# and every header the sources may include (rebuild/include, rebuild/src, the generated code's own headers), so a
# rebuild compiles only what changed.  They run on all cores.
CACHE = os.environ.get('DECOMP_BUILD_CACHE', os.path.expanduser('~/.cache/decomp_build'))
_deps = []


def header_digest(dirs):
    h = hashlib.sha256()
    for d in dirs:
        for f in sorted(glob.glob(os.path.join(d, '**', '*.h'), recursive=True) +
                        glob.glob(os.path.join(d, '**', '*.inc'), recursive=True)):
            h.update(f.encode() + b'\0' + open(f, 'rb').read())
    _deps[:] = [h.hexdigest()]


def cached_run(cmd, src, out=None):
    """run a compiler command on src: its stdout, or (out given) the file it writes, from the cache if it ran before"""
    key = hashlib.sha256(json.dumps([[x if x != out else 'OUT' for x in cmd], _deps]).encode() +
                         open(src, 'rb').read()).hexdigest()
    path = os.path.join(CACHE, key[:2], key)
    if os.path.exists(path):
        if out:
            shutil.copyfile(path, out)
            return ''
        return open(path, encoding='utf-8').read()
    res = run(cmd)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.%d' % os.getpid()
    if out:
        shutil.copyfile(out, tmp)
    else:
        open(tmp, 'w', encoding='utf-8').write(res)
    os.replace(tmp, path)
    return res


def pmap(f, items):
    """f over items on all cores, in order"""
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(os.cpu_count() or 4) as ex:
        return list(ex.map(f, items))


def load_functions(game):
    """addr -> (size, regs_in, retpop, clobber)"""
    f = {}
    for l in open(os.path.join(SYMS, '%s_functions.tsv' % game)):
        if l.startswith('#'):
            continue
        a, size, regs, retpop, clob = l.rstrip('\n').split('\t')[:5]
        f[int(a, 16)] = (int(size), sorted((r for r in regs.split(',') if r and r != 'EBP'), key=REG_ORDER.index),
                         0 if retpop == '?' else int(retpop or 0), set(x for x in clob.split(',') if x))
    return f


TRUSTED = {'vtable', 'bytes', 'strings', 'luatable', 'lunar', 'luaglobal', 'export', 'attfix', 'manual'}


def load_map(name, how=None):
    m = {}
    path = os.path.join(SYMS, name)
    if os.path.exists(path):
        for l in open(path):
            if l.startswith('#') or not l.strip():
                continue
            p = l.split('\t')
            m[int(p[0], 16)] = int(p[1], 16)
            if how is not None:
                how[int(p[0], 16)] = p[2].strip() if len(p) > 2 else ''
    return m


WIDE_PARAM = re.compile(r'\b(double|long\s+long|longlong|ulonglong|undefined8|__int64|qword|float10)\b')


def split_params(text):
    """'(lua_State *L, int narg)' -> number of 4-byte stack slots the parameters take: an 8-byte one (double,
    long long, undefined8) takes two, a string by value seven.  Counted as one, an adapter copied a dword too few of 0x48C2D0's arguments
    (byte, short, undefined8, int, int: 24 bytes), its ret 24 then took an argument for the return address."""
    t = text.strip()
    if t.startswith('('):
        t = t[1:t.rfind(')')]
    t = t.strip()
    if t in ('', 'void'):
        return 0
    depth, cur, parts = 0, '', []
    for c in t:
        if c in '(<[':
            depth += 1
        elif c in ')>]':
            depth -= 1
        if c == ',' and depth == 0:
            parts.append(cur)
            cur = ''
        else:
            cur += c
    parts.append(cur)
    def slots(p_):
        if '*' in p_ or '(' in p_:
            return 1
        if 'StrByValue' in p_:
            return 7            # a std::string by value (ghidra/ByValueParams.java): 28 bytes, 0x4F7430
        return 2 if WIDE_PARAM.search(p_) else 1
    return sum(slots(p_) for p_ in parts)


STACK_ONLY = set()      # DECOMP_STACK: replacements taking every argument on the stack (decomp.h)
# replacements a --toggle build never switches off: the entries of the Lua library, whose original code does not work
# on the state the new one made
ALWAYS_ON = set()


def scan_sources(files, cflags):
    """DECOMP annotations: (attt_addr, qualified name, param count, is_member) and ORIG_* prototypes, from the
    preprocessed sources (so #if DECOMP_GAME_ATTT / DECOMP_GAME_VALK is honoured)."""
    decomp, protos = [], {}
    conv_of = {'__cdecl': 'FN', '__stdcall': 'STDCALL', '__fastcall': 'FASTCALL', '__thiscall': 'THISCALL'}
    def pre(fn):
        extra = ['-x', 'c++', '-std=c++17'] if fn.endswith('.cpp') else ['-x', 'c', '-std=c11']
        return cached_run(['clang'] + cflags + extra + ['-DDECOMP_SCAN', '-E', '-P', fn], fn)
    for fn, src in zip(files, pmap(pre, files)):
        for m in re.finditer(r'__decomp_marker__\(\s*([0-9A-Fa-f]{8})\s*\)\s*([^{;]*?)\b([A-Za-z_][\w:~<>]*)\s*(\((?:[^()]|\([^()]*\))*\))', src):
            addr, name, params = int(m.group(1), 16), m.group(3), m.group(4)
            decomp.append((addr, name, split_params(params), '::' in name, fn))
            if '__decomp_stack__' in m.group(2):
                STACK_ONLY.add(addr)
            if os.path.basename(os.path.dirname(fn)) == 'lua51':
                ALWAYS_ON.add(addr)
        for m in re.finditer(r'(__cdecl|__stdcall|__fastcall|__thiscall)\s+sub_([0-9A-Fa-f]{8})\s*(\((?:[^()]|\([^()]*\))*\))', src):
            protos[int(m.group(2), 16)] = (conv_of[m.group(1)], split_params(m.group(3)))
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


_demangled = {}


def demangle_all(syms):
    """demangle many MSVC names with one llvm-undname run (it prints: input, demangled, empty line)"""
    todo = sorted(set(s for s in syms if s.startswith('?') and s not in _demangled))
    if todo:
        out = subprocess.run(['llvm-undname'], input='\n'.join(todo) + '\n', capture_output=True, text=True).stdout
        lines = out.split('\n')
        i = 0
        while i + 1 < len(lines):
            src, d = lines[i], lines[i + 1]
            if src in todo:
                m = re.search(r'([\w:~<>]+)\(', d)
                _demangled[src] = m.group(1) if m else d
                i += 3
            else:
                i += 1
        for s in todo:
            _demangled.setdefault(s, s)


def demangle(sym):
    if not sym.startswith('?'):
        return sym.lstrip('_@').split('@')[0]
    if sym not in _demangled:
        demangle_all([sym])
    return _demangled[sym]


def symbol_conv(sym, member):
    """calling convention of a compiled function from its MSVC decorated name"""
    cc = {'A': 'cdecl', 'E': 'thiscall', 'G': 'stdcall', 'I': 'fastcall'}
    if sym.startswith('?'):
        m = re.search(r'@@(Y)([AEGI])', sym)
        if m:
            return cc[m.group(2)]
        m = re.search(r'@@([QAIUMEOGWKSC])([A-D]?)([AEGI])', sym)
        if m:
            return cc[m.group(3)]
        return 'thiscall' if member else 'cdecl'
    if sym.startswith('@'):
        return 'fastcall'
    if re.match(r'^_\w+@\d+$', sym):
        return 'stdcall'
    return 'cdecl'


def adapter_asm(name, target, conv, regs, nstack, retpop, preserve):
    """Entry used by original callers.  conv 'cdecl': target(regs..., stack args...), caller pops;
    conv 'thiscall': ECX passes through, target pops the stack args.  Volatile registers in preserve are kept."""
    a = ['\t.globl\t_%s' % name, '_%s:' % name]
    saved = [r for r in ('EAX', 'ECX', 'EDX') if r in preserve]
    for r in saved:
        a.append('\tpushl\t%%%s' % r.lower())
    off = 4 * len(saved) + 4 + 4 * (nstack - 1)
    for i in range(nstack):
        a.append('\tpushl\t%d(%%esp)' % off)
    if conv == 'cdecl':
        for r in reversed(regs):
            a.append('\tpushl\t%%%s' % r.lower())
    a.append('\tcalll\t"%s"' % target)
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
    ap.add_argument('--toggle', action='store_true', help='replacements switched on at start-up (toggle.c, '
                    'decomp_toggle.txt next to the exe): bisection without a new build for each step')
    ap.add_argument('--only', help='comma-separated source files (default: all of rebuild/src)')
    ap.add_argument('--auto', help='folder made by tools/autodecomp.py for this game (addresses of the game itself)')
    ap.add_argument('-D', dest='defines', action='append', default=[], help='preprocessor define for the sources '
                    '(e.g. -D DECOMP_DEBUG_LOG: engine errors go to OutputDebugString)')
    ap.add_argument('--auto-list', help='only these auto-decompiled functions (file with one address per line)')
    ap.add_argument('--auto-exclude', help='not these auto-decompiled functions (e.g. bad.txt of tools/autobisect.py)')
    a = ap.parse_args()

    pe = PE(a.exe)
    game = GAMES.get(pe.pe.FILE_HEADER.TimeDateStamp)
    if not game:
        sys.exit('unknown exe (TimeDateStamp %08X)' % pe.pe.FILE_HEADER.TimeDateStamp)
    work = os.path.join(os.path.dirname(os.path.abspath(a.out)), 'work_' + game)
    os.makedirs(work, exist_ok=True)
    funcs = load_functions(game)
    machine_funcs = dict(funcs)    # as the machine code is; funcs may get the generated code's register lists
    native_refs = set()     # filled for auto-decompiled code of Valkyrie (its own addresses)
    fhow = {}
    fmap = load_map('attt2valk.tsv', fhow) if game == 'valk' else None
    dmap = load_map('attt2valk_data.tsv') if game == 'valk' else None

    def gaddr(x, data=False):
        if game == 'attt' or (x in native_refs):
            return x
        m = (dmap if data else fmap) or {}
        if x not in m:
            sys.exit('no Valkyrie address for AttT %08X; add it to symbols/attt2valk%s.tsv' % (x, '_data' if data else ''))
        return m[x]

    # src/fixed: generated functions fixed by hand (tools/autodecomp.py --draft), built with the generated code
    fixed_dir = os.path.join(HERE, 'src', 'fixed')
    files = sorted(f for f in glob.glob(os.path.join(HERE, 'src', '**', '*.c'), recursive=True) +
                   glob.glob(os.path.join(HERE, 'src', '**', '*.cpp'), recursive=True)
                   if os.path.dirname(f) != fixed_dir)
    if a.only:
        files = [f for f in files if os.path.basename(f) in a.only.split(',')]

    mingw_inc = os.environ.get('MINGW_INCLUDE', '/usr/i686-w64-mingw32/include')
    cflags = ['--target=i686-pc-windows-msvc', '-O2', '-march=pentium4', '-msse2', '-fms-extensions',
              '-fno-builtin', '-ffreestanding', '-fno-stack-protector', '-I', os.path.join(HERE, 'include'),
              # Win32 / Direct3D 9 declarations from mingw-w64 work with the MSVC ABI this way
              '-fgnuc-version=4.2.1', '-D_X86_', '-DWIN32_LEAN_AND_MEAN', '-isystem', mingw_inc,
              '-I', os.path.join(HERE, 'src'), '-D', 'DECOMP_GAME_%s=1' % game.upper()] + ['-D' + d for d in a.defines]
    header_digest([os.path.join(HERE, 'include'), os.path.join(HERE, 'src')] + ([os.path.abspath(a.auto)] if a.auto else []))
    decomp, protos = scan_sources(files, cflags)
    # compile
    lua_dir = os.path.join(HERE, 'src', 'lua51')

    def compile_src(fn):
        obj = os.path.join(work, os.path.relpath(fn, os.path.join(HERE, 'src')).replace(os.sep, '_') + '.obj')
        if os.path.dirname(fn) == lua_dir:
            # Lua 5.1.2 as the game built it: C++ (an error is a C++ exception through the game's frames) and
            # x87 arithmetic, whose precision the game sets to single (src/lua51/decomp_entries.c)
            fl = [x for x in cflags if x not in ('-march=pentium4', '-msse2')]
            # (the runtime is MSVCR80: time_t is 64 bits, os.time calls _time64 as the original does)
            cached_run(['clang'] + fl + ['-march=pentium-mmx', '-mfpmath=387', '-x', 'c++', '-std=c++17', '-fexceptions',
                                         '-fcxx-exceptions', '-w', '-D__MSVCRT_VERSION__=0x0800', '-D__USE_MINGW_ANSI_STDIO=0',
                                         '-D__MINGW_USE_VC2005_COMPAT',
                                         '-include', os.path.join(lua_dir, 'decomp_crt.h'),
                                         '-c', fn, '-o', obj], fn, obj)
            return obj
        extra = ['-std=c++17', '-fno-exceptions', '-fno-rtti'] if fn.endswith('.cpp') else ['-std=c11']
        cached_run(['clang'] + cflags + extra + ['-c', fn, '-o', obj], fn, obj)
        return obj
    objs = pmap(compile_src, files)
    native = set()          # DECOMP addresses that are already addresses of this game (auto-decompiled code)
    raw_fixed = set()       # src/fixed functions marked '/* @raw */': naked code taking the original's place as is
    custom_auto = {}        # auto functions written as cdecl with the register parameters first
    if a.auto:
        allow = None
        if a.auto_list:
            allow = set(int(l.split()[0], 16) for l in open(a.auto_list) if l.strip() and not l.startswith('#'))
        if a.auto_exclude:
            if allow is None:
                allow = set(int(l.split('\t')[0], 16) for l in open(os.path.join(a.auto, 'functions.tsv'))
                            if l.split('\t')[1] == 'compiled')
            allow -= set(int(l.split()[0], 16) for l in open(a.auto_exclude) if l.strip() and not l.startswith('#'))
        # the functions fixed by hand replace their generated versions; '/* @conv REGS POP */' in them is the
        # prototype as convs.tsv would give it
        fixed = {}
        for fx in sorted(glob.glob(os.path.join(fixed_dir, 'f_*.c'))) if game == 'attt' else []:
            fixed[int(os.path.basename(fx)[2:10], 16)] = fx
        if fixed:
            if allow is None:
                allow = set(int(l.split('\t')[0], 16) for l in open(os.path.join(a.auto, 'functions.tsv'))
                            if l.split('\t')[1] == 'compiled')
            allow -= set(fixed)
        # x87 arithmetic like the original (its float code is x87; SSE rounds every step to float)
        # (the machine code's semantics, not C's: integers wrap, memory is accessed through any type, and pointers
        # are plain addresses: 0x470150 counts bytes down in a pointer to NULL, a loop clang made endless otherwise)
        aflags = ['--target=i686-pc-windows-msvc', '-O1', '-march=pentium-mmx', '-mfpmath=387', '-fms-extensions', '-ffreestanding',
                  '-fno-builtin', '-fno-stack-protector', '-fwrapv', '-fno-strict-aliasing', '-fno-delete-null-pointer-checks',
                  '-x', 'c', '-std=gnu11', '-w',
                  '-Wno-error=int-conversion', '-Wno-error=incompatible-pointer-types',
                  '-Wno-error=incompatible-function-pointer-types', '-Wno-error=int-to-pointer-cast', '-Wno-error=return-type',
                  '-I', os.path.join(HERE, 'include'), '-I', os.path.abspath(a.auto)]
        # the prototypes the generated code uses: the register lists in their parameter order (they may name
        # registers the function does not read, which is harmless) and the ret pop
        for l in open(os.path.join(a.auto, 'convs.tsv')):
            if l.startswith('#'):
                continue
            q = l.rstrip('\n').split('\t')
            ad = int(q[0], 16)
            size, old, oldpop, clob = funcs.get(ad, (0, [], 0, {'EAX', 'ECX', 'EDX'}))
            new = [r for r in q[1].split(',') if r]
            if (ad in protos or any(gaddr(d[0]) == ad for d in decomp)) and (new, int(q[2])) != (old, oldpop):
                sys.exit('%08X: the hand-written code and the generated code see different conventions' % ad)
            funcs[ad] = (size, new, int(q[2]), clob)
        hand = set(d[0] for d in decomp) if game == 'attt' else set(gaddr(d[0]) for d in decomp)
        srcs = []
        for fn in sorted(glob.glob(os.path.join(a.auto, 'auto_*.c'))):
            src = fn
            if allow is not None:
                text = open(fn, encoding='utf-8').read()
                parts = re.split(r'(?=^/\* @func [0-9A-F]{8}(?: custom)? \*/$)', text, flags=re.M)
                head, funcs_ = parts[0], parts[1:]
                keep = [x for x in funcs_ if int(x[9:17], 16) in allow]
                if not keep:
                    continue
                src = os.path.join(work, 'sel_' + os.path.basename(fn))
                open(src, 'w', encoding='utf-8').write(head + ''.join(keep))
            srcs.append((fn, src))
        for ad, fx in fixed.items():
            if '/* @raw */' in open(fx, encoding='utf-8').read():
                raw_fixed.add(ad)       # (a naked function: original callers jump straight to it, no adapter)
            m = re.search(r'/\* @conv (\S+) (\d+) \*/', open(fx, encoding='utf-8').read())
            if m:
                size, old, oldpop, clob = funcs.get(ad, (0, [], 0, {'EAX', 'ECX', 'EDX'}))
                funcs[ad] = (size, [r for r in m.group(1).split(',') if r != '-'], int(m.group(2)), clob)
            srcs.append((fx, fx))

        def scan_compile(fs):
            fn, src = fs
            obj = os.path.join(work, 'auto_' + os.path.basename(fn) + '.obj')
            cached_run(['clang'] + aflags + ['-c', src, '-o', obj], src, obj)
            return cached_run(['clang'] + aflags + ['-DDECOMP_SCAN', '-E', '-P', src], src), obj
        for (fn, src), (pre, obj) in zip(srcs, pmap(scan_compile, srcs)):
            for m in re.finditer(r'^/\* @func ([0-9A-F]{8}) custom \*/$', open(src, encoding='utf-8').read(), flags=re.M):
                custom_auto[int(m.group(1), 16)] = True
            for m in re.finditer(r'__decomp_marker__\(\s*([0-9A-Fa-f]{8})\s*\)\s*([^{;]*?)\b(f_[0-9A-F]{8})\s*(\((?:[^()]|\([^()]*\))*\))', pre):
                ad = int(m.group(1), 16)
                if ad in hand:
                    continue
                cm = re.search(r'__(cdecl|stdcall|fastcall|thiscall)', m.group(2))
                decomp.append((ad, m.group(3), split_params(m.group(4)), False, src, cm.group(1) if cm else 'cdecl'))
                native.add(ad)
            for m in re.finditer(r'(__cdecl|__stdcall|__fastcall|__thiscall)\s+sub_([0-9A-Fa-f]{8})\s*(\((?:[^()]|\([^()]*\))*\))', pre):
                conv_of = {'__cdecl': 'FN', '__stdcall': 'STDCALL', '__fastcall': 'FASTCALL', '__thiscall': 'THISCALL'}
                protos.setdefault(int(m.group(2), 16), (conv_of[m.group(1)], split_params(m.group(3))))
            objs.append(obj)
    rt = os.path.join(work, 'rt_support.obj')
    run(['clang'] + cflags + ['-c', os.path.join(HERE, 'rt_support.c'), '-o', rt])
    objs.append(rt)
    if a.toggle:
        to = os.path.join(work, 'toggle.obj')
        run(['clang'] + cflags + ['-c', os.path.join(HERE, 'toggle.c'), '-o', to])
        objs.append(to)

    defined, undefined = set(), set()
    for o in objs:
        d, u = nm_symbols(o)
        defined |= set(d)
        undefined |= set(u)
    undefined -= defined

    syms, repl, asm = [], [], ['\t.text']
    skipped = []
    # replacements
    demangle_all(list(defined) + list(undefined))
    by_name = {}
    for s in defined:
        by_name.setdefault(demangle(s), []).append(s)
    for entry in decomp:
        addr, name, nparams, member, fn = entry[:5]
        forced_conv = entry[5] if len(entry) > 5 else None
        cands = by_name.get(name) or by_name.get(name.split('::')[-1]) or []
        cands = [c for c in cands if not c.startswith('_sub_') and not c.startswith('raw_')]
        if len(cands) != 1:
            sys.exit('%s: cannot find the compiled symbol of %s (candidates: %s)' % (fn, name, cands))
        sym = cands[0]
        ga = addr if addr in native else gaddr(addr)
        if game == 'valk' and addr not in native and fhow.get(addr) not in TRUSTED:
            sys.exit('%s: %s: the Valkyrie match of %08X is only "%s"; check it and mark it "manual" in '
                     'symbols/attt2valk.tsv, or exclude the function with #if DECOMP_GAME_ATTT'
                     % (fn, name, addr, fhow.get(addr)))
        if ga in raw_fixed:
            repl.append((ga, sym))
            continue
        size, regs, retpop, clob = funcs.get(ga, (0, [], 0, {'EAX', 'ECX', 'EDX'}))
        if addr in STACK_ONLY:
            regs = []
        preserve = {'EAX', 'ECX', 'EDX'} - clob      # LTCG callers may use a register argument again after the call
        conv = forced_conv or symbol_conv(sym, member)
        if conv == 'thiscall':
            nstack = nparams if member else nparams - 1     # a C function names this as its first parameter
            direct = set(regs) <= {'ECX'} and retpop == 4 * nstack
        elif conv == 'cdecl':
            nstack = nparams - len(regs)
            direct = not regs and retpop == 0
            if addr in native and regs and forced_conv == 'cdecl' and not custom_auto.get(addr, False):
                skipped.append((addr, 'registers the prototype does not take'))
                continue
        else:
            nstack = nparams
            direct = (conv == 'stdcall' and not regs and retpop == 4 * nstack) or \
                     (conv == 'fastcall' and set(regs) <= {'ECX', 'EDX'} and retpop == 4 * max(0, nstack - 2))
        if fn.startswith(fixed_dir) and conv in ('thiscall', 'stdcall') and retpop != 4 * nstack:
            # (the adapter counts parameters: one passing a structure by value would be taken as one dword)
            sys.exit('%s: %s pops %d bytes but has %d stack parameters; write every stack parameter as a dword'
                     % (fn, name, retpop, nstack))
        if direct and not preserve:
            repl.append((ga, sym))
            continue
        if conv == 'stdcall' and not regs:
            conv = 'thiscall'      # same stack handling: the target pops its stack arguments, no registers
        elif conv == 'fastcall' and set(regs) <= {'ECX', 'EDX'}:
            conv, nstack = 'thiscall', max(0, nstack - 2)   # ECX and EDX pass through the adapter untouched
            regs = [r for r in regs if r != 'EDX']
        if conv not in ('cdecl', 'thiscall') or (conv == 'thiscall' and not set(regs) <= {'ECX'}) or \
                (conv == 'cdecl' and addr in native and regs and nstack < 0):
            if addr in native:      # the decompiler's prototype does not fit the machine code: leave the original
                skipped.append((addr, 'convention'))
                continue
            sys.exit('%s: %s: original %08X takes %s and pops %d bytes; write the replacement as a cdecl function '
                     'with the register parameters first (%s)' % (fn, name, ga, ','.join(regs) or 'no registers',
                                                                   retpop, ', '.join(REG_ORDER)))
        ad = 'adp_%08X' % addr
        asm += adapter_asm(ad, sym, conv, regs if conv == 'cdecl' else [], max(nstack, 0), retpop, preserve)
        repl.append((ga, ad))
    # C++ declarations of original functions (methods not decompiled yet): resolved by name through the
    # symbol tables of the game (symbols/attt.sym and attt_manual.sym, AttT addresses)
    byaddr = {}
    for fn_ in ('attt.sym', 'attt_manual.sym'):          # the manual names win (and need no regeneration)
        for l in open(os.path.join(SYMS, fn_), encoding='utf-8'):
            if l[0] in '#S' or not l.strip():
                continue
            b_ = l.split('#')[0].split(None, 2)
            if len(b_) == 3 and b_[1] == 'f':
                byaddr[int(b_[0], 16)] = b_[2].strip().replace(' ', '_')
    names = {}
    resolved = set()
    for ad_, n_ in byaddr.items():
        names.setdefault(n_, []).append(ad_)
    for s in sorted(undefined):
        if not s.startswith('?') and not (s.startswith('__a') or s.startswith('__ftol')):
            continue
        q = demangle(s) if s.startswith('?') else s[1:]
        cands = names.get(q, [])
        if len(cands) > 1:
            sys.exit('%s is ambiguous in the symbol tables: %s' % (q, ' '.join('%08X' % c for c in cands)))
        if cands:
            ga = gaddr(cands[0])
            regs = machine_funcs.get(ga, (0, [], 0, set()))[1]
            if [r for r in regs if r != 'ECX']:
                sys.exit('%s (%08X) has an LTCG register convention: call it through ORIG_FN' % (q, cands[0]))
            # (exe2obj adds the leading underscore of a C name: '__allrem' of a 64-bit remainder is '_allrem')
            syms.append((ga, s if s[0] in '?@' else s[1:]))
            resolved.add(s)
    # references to originals
    for s in sorted(undefined):
        m = re.match(r'^[_@]?(sub|d)_([0-9A-Fa-f]{8})(@\d+)?$', s)
        if not m:
            continue
        kind, addr = m.group(1), int(m.group(2), 16)
        if kind == 'd':
            syms.append((gaddr(addr, True), s[1:] if s.startswith('_') else s))
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

    with open(os.path.join(work, 'always_on.txt'), 'w') as f:
        f.write(''.join('%08X\n' % x for x in sorted(ALWAYS_ON)))
    run([sys.executable, '-I', os.path.join(TOOLS, 'exe2obj.py'), a.exe, work,
         '--syms', os.path.join(work, 'syms.txt'), '--replace', os.path.join(work, 'replace.txt')] +
        (['--toggle', '--always-on', os.path.join(work, 'always_on.txt')] if a.toggle else []))
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
        if re.match(r'^[_@]?(sub|d|raw)_[0-9A-Fa-f]{8}', s_):
            continue
        if s_.startswith('__imp_'):
            n = s_[6:]
        elif re.match(r'^_\w+@\d+$', s_):
            n = s_                         # stdcall call through the import thunk
        elif re.match(r'^_[A-Za-z_]\w*$', s_) and (s_[1:] in have or s_[1:] in extra_map):
            n = s_                         # a C runtime function called directly (the Lua sources: strcmp)
        else:
            continue
        if not n.startswith('?'):
            n = n[1:]                      # C names carry the extra underscore
        if n in have:
            continue
        base = n.split('@')[0] if '@' in n and not n.startswith('?') else None
        if '_' + n in have:                # imported with the decorated name itself (Miles, Bink: _AIL_x@8)
            dll = open(have['_' + n]).read().splitlines()[0].split()[1]
            add.setdefault(dll, []).append((n, '_' + n))
            have[n] = have['_' + n]
            continue
        if base and base in have:          # decorated stdcall name of a function the exe imports undecorated
            dll = open(have[base]).read().splitlines()[0].split()[1]
            add.setdefault(dll, []).append((n, base))
            have[n] = have[base]
            continue
        dll = extra_map.get(n) or extra_map.get(base or '') or ('MSVCP80.dll' if 'std@@' in n else None)
        if not dll:
            sys.exit('new code imports %s: add "%s <dll>" to rebuild/imports_extra.txt' % (n, n))
        if base and base not in have:      # 'name@N == name' refers to an export 'name' of the .def: add it too
            add.setdefault(dll, []).append((base, base))
            have[base] = dll
        add.setdefault(dll, []).append((n, base or n))
        have[n] = dll
    for dll, names in add.items():
        d = os.path.join(work, 'imports', dll.lower().replace('.dll', '') + '.def')
        if not os.path.exists(d):
            open(d, 'w').write('LIBRARY %s\nEXPORTS\n' % dll)
        with open(d, 'a') as f:
            for n, imp in names:
                f.write('  %s == %s\n' % (n, imp))
    # direct calls of imported functions get the linker's jmp thunks at the end of .text: they fit into the
    # unused tail of the original .text page, so .rdata does not move (checked after linking)
    if len(asm) > 1:
        gs = os.path.join(work, 'glue.s')
        open(gs, 'w').write('\n'.join(asm) + '\n')
        go = os.path.join(work, 'glue.obj')
        run(['clang', '--target=i686-pc-windows-msvc', '-c', gs, '-o', go])
        objs.append(go)
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
    if a.toggle:
        rsp = ['/entry:decomp_entry' if x == '/entry:orig_entry' else x for x in rsp]
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
    if skipped:
        with open(os.path.join(work, 'skipped.txt'), 'w') as f:
            for ad, why in skipped:
                f.write('%08X\t%s\n' % (ad, why))
        print('%d auto-decompiled functions left out (prototype does not fit; see %s)' % (len(skipped), os.path.join(work, 'skipped.txt')))
    print('%s: %d replaced functions, %d original symbols used -> %s' % (game, len(repl), len(syms), a.out))


if __name__ == '__main__':
    main()
