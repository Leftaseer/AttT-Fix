#!/usr/bin/env python3
"""Classify every function of an analyzed game exe: where its code comes from and what kind of code it is.

The rebuild of ATThrone.exe keeps the original .text and replaces single functions (DECOMP markers) with
hand-written or generated code; the function inventory is symbols/<game>_functions.tsv (one row per function,
its size = the distance to the next entry).  This tool joins the inventory with

  * the DECOMP markers of rebuild/src (engine = C++, lua51 = Lua 5.1 sources, fixed = hand-written C),
  * the DECOMP markers of the auto-decompiled directory (rebuild/build.py --auto),
  * the build's replace.txt (the ground truth of what was replaced, if the build has run),
  * the auto decompiler's functions.tsv (compiled / rejected + reason),
  * the symbol tables (names and their tags: lua-lib, rtti, slot, ctor, ...),
  * optionally the original exe: disassembles every function for call targets, import calls and the entry
    patterns of compiler glue (import thunks, EH funclets, SEH prologues),

and prints an origin table (who wrote it), a nature table (what it is: Lua library, Lua binding, RTTI/vtable,
constructor/destructor/singleton, thunk, EH funclet, compiler/CRT glue, stub, game logic, data), the untouched
game functions grouped by the auto pipeline's verdict and the largest ones (the hand-translation backlog), and
the buckets that are better replaced wholesale (Lua library from its sources) or left as they are (CRT glue).

usage: classify.py [EXE] [--functions TSV] [--sym S.sym ...] [--src DIR] [--auto DIR] [--replace TSV]
                   [--lua-range LO-HI] [--crt-range LO-HI] [--top N] [--csv OUT.tsv] [--json OUT.json]

EXE is optional: without it the tool still classifies by symbols and sources, but not by the machine code
(no inbound call counts, no thunk/funclet/SEH/data detection of unnamed functions)."""
import argparse
import collections
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

TAG_RX = re.compile(r'\s*([a-z][a-z0-9-]*)')
KNOWN_TAGS = {'rtti', 'rtti-shared', 'rtti-dtor', 'rtti-ddtor', 'slot', 'ctor', 'singleton',
              'lua-lib', 'lua-method', 'lua-global', 'manual', 'stub', 'export'}
LUA_NAME_RX = re.compile(r'^(?:lua[A-Z]_|luaL_|lua_|luaopen_|math_)')
LUA_BINDING_RX = re.compile(r'^(?:Lua_|LuaGlobal_)')

# entry bytes that only a compiler-generated helper or a non-instruction starts with (the false functions
# AddMissingFunctions.java makes at a 0xCC byte inside a 'mov eax, imm32' of the EH thunk tables)
JUNK_ENTRY = {'test', 'or', 'adc', 'sbb', 'xchg', 'movsb', 'movsw', 'movsd', 'cmpsb', 'scasb', 'stosb', 'lodsb',
              'clc', 'stc', 'cmc', 'leave', 'retf', 'iret', 'iretd', 'int', 'int3', 'fistp', 'fist', 'fstp',
              'shl', 'shr', 'sal', 'sar', 'bound', 'in', 'out', 'pushf', 'popf', 'lcall', 'ljmp', 'daa', 'das',
              'aaa', 'aas', 'hlt', 'cli', 'sti', 'cld', 'std', 'lahf', 'sahf', 'xlatb', 'popa', 'pusha'}
MSVC_DLLS = ('MSVCP80.dll', 'MSVCR80.dll')

# nature order for the report: first the replaceable/known kinds, then the compiler glue, then game logic
NATURES = ['lua-lib', 'lua-binding', 'rtti', 'slot', 'lifecycle', 'stub', 'export',
           'thunk', 'funclet', 'crt', 'data', 'game']
ORIGINS = ['engine', 'lua51', 'fixed', 'auto', 'untouched']
BACKLOG_NATURES = {'lua-binding', 'rtti', 'slot', 'lifecycle', 'stub', 'export', 'game'}


def read_functions(path):
    rows = []
    for line in open(path, encoding='utf-8', errors='replace'):
        if not line.strip() or line[0] == '#':
            continue
        p = line.split('\t')
        rows.append({'a': int(p[0], 16), 'size': int(p[1])})
    rows.sort(key=lambda r: r['a'])
    return rows


def read_syms(paths):
    """addr -> [name, tag]; the first file wins (attt.sym already merges the others), a tagless later note
    does not erase the tag of an earlier one"""
    out = {}
    for path in paths:
        if not os.path.exists(path):
            continue
        for line in open(path, encoding='utf-8', errors='replace'):
            line = line.strip()
            if not line or line[0] == '#' or line.startswith('SLOT '):
                continue
            body, _, note = line.partition('#')
            p = body.split(None, 2)
            if len(p) < 3 or p[1] != 'f':
                continue
            addr = int(p[0], 16)
            m = TAG_RX.match(note)
            tag = m.group(1) if m and m.group(1) in KNOWN_TAGS else ''
            cur = out.setdefault(addr, [p[2].strip(), tag])
            if not cur[1] and tag:
                cur[1] = tag
    return out


def scan_markers(root):
    """relative top directory (engine / lua51 / fixed / ...) -> set of DECOMP addresses in its .c/.cpp files"""
    found = collections.defaultdict(set)
    rx = re.compile(r'\bDECOMP(?:_STACK)?\s*\(\s*([0-9A-Fa-f]{8})\s*\)')
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if not fn.endswith(('.c', '.cpp')):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, root)
            unit = rel.split(os.sep, 1)[0] if os.sep in rel else ''
            with open(path, encoding='utf-8', errors='replace') as f:
                for m in rx.finditer(f.read()):
                    found[unit].add(int(m.group(1), 16))
    return found


def read_replace(path):
    out = {}
    if path and os.path.exists(path):
        for line in open(path, encoding='utf-8', errors='replace'):
            p = line.split()
            if len(p) >= 2:
                out[int(p[0], 16)] = p[1]
    return out


def read_statuses(auto):
    out = {}
    path = os.path.join(auto, 'functions.tsv') if auto else None
    if path and os.path.exists(path):
        for line in open(path, encoding='utf-8', errors='replace'):
            p = line.rstrip('\n').split('\t')
            if len(p) < 2 or not re.match(r'^[0-9A-Fa-f]{8}$', p[0]):
                continue
            out[int(p[0], 16)] = p[1] + (': ' + p[2] if len(p) > 2 and p[2] else '')
    return out


def analyze_machine(exe, rows, lua_lo, lua_hi, crt_lo, crt_hi):
    """Per-row machine facts: first mnemonic, SEH entry, thunk/funclet shape, calls to imports, calls into the
    game code, inbound call/jump references."""
    sys.path.insert(0, HERE)
    from pe import PE
    import capstone
    from capstone.x86 import X86_OP_IMM, X86_OP_MEM

    p = PE(exe)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    starts = {r['a']: i for i, r in enumerate(rows)}
    t0, t1 = p.text_range()

    for r in rows:
        r.update(first='', seh=False, thunk=False, funclet=False, inbound=0, imports=collections.Counter(),
                 game_calls=0, msvc_calls=0, junk=False)
    for r in rows:
        a, size = r['a'], r['size']
        if not (t0 <= a < t1):
            continue
        code = p.read(a, min(size, 64)) or b''
        head = list(md.disasm(code, a))[:6]
        if not head:
            r['junk'] = True
            continue
        r['first'] = head[0].mnemonic
        r['junk'] = head[0].mnemonic in JUNK_ENTRY
        b = p.read(a, 12) or b''
        r['seh'] = b[:2] == b'\x6a\xff' and b[4:6] == b'\x68' and b[9:11] == b'\x64\xa1' or b[:2] == b'\x64\xa1'

    for r in rows:
        a, size = r['a'], r['size']
        if not (t0 <= a < t1):
            continue
        code = p.read(a, size) or b''
        ins = []
        for i in md.disasm(code, a):
            if i.address >= a + size:
                break
            ins.append(i)
            if len(ins) > 20000:      # a broken 'function' of mostly data: enough evidence either way
                break
        if not ins:
            continue
        head = ins[:6]
        # compiler glue: a jump thunk (import/forwarding/EH 'mov eax, imm; jmp'), an unwind helper
        # ('mov ecx, [ebp-x]; jmp'), or read of the caller's frame before a frame of its own (an EH funclet)
        has_prologue = any(i.mnemonic == 'mov' and i.op_str.startswith('ebp, esp') for i in head)
        reads_frame = any('[ebp - ' in i.op_str for i in head)
        jumps = sum(1 for i in ins if i.mnemonic == 'jmp')
        calls = sum(1 for i in ins if i.mnemonic == 'call')
        if ins[0].mnemonic == 'jmp' and len(ins) <= 2:
            r['thunk'] = True
        elif size <= 24 and jumps and not calls and 'jmp' in [i.mnemonic for i in head]:
            r['thunk'] = True
        elif reads_frame and not has_prologue:
            r['funclet'] = True
        # calls: imports (through the IAT) and the game's own code; the target row of a call counts as a caller
        for i in ins:
            if i.mnemonic not in ('call', 'jmp'):
                continue
            o = i.operands[0]
            if o.type == X86_OP_IMM:
                target = o.imm & 0xffffffff
                if i.mnemonic == 'call' and lua_hi <= target < crt_lo:
                    r['game_calls'] += 1
                j = starts.get(target)
                if j is not None:
                    rows[j]['inbound'] += 1
            elif o.type == X86_OP_MEM and o.mem.base == 0:
                q = o.mem.disp & 0xffffffff
                if q in p.imports:
                    dll, name = p.imports[q]
                    r['imports'][dll + '!' + name] += 1
                    if dll in MSVC_DLLS:
                        r['msvc_calls'] += 1
    for r in rows:
        # a replaced row was decompiled, so a 'test'/'or' entry is a real prologue and not a false function
        r['data_like'] = (r['junk'] and r['size'] >= 16 and r['inbound'] == 0 and not r['replaced'])


def nature_of(r, syms, lua_lo, lua_hi, crt_lo, crt_hi):
    name, tag = syms.get(r['a'], ('', ''))
    if tag == 'lua-lib' or LUA_NAME_RX.match(name):
        return 'lua-lib'
    if tag in ('lua-method', 'lua-global') or LUA_BINDING_RX.match(name):
        return 'lua-binding'
    if tag in ('rtti', 'rtti-shared'):
        return 'rtti'
    if tag == 'slot':
        return 'slot'
    if tag in ('ctor', 'singleton', 'rtti-dtor', 'rtti-ddtor'):
        return 'lifecycle'
    if tag == 'stub':
        return 'stub'
    if tag == 'export':
        return 'export'
    if not name and lua_lo <= r['a'] < lua_hi:
        return 'lua-lib'
    if r.get('thunk'):
        return 'thunk'
    if r.get('funclet'):
        return 'funclet'
    if crt_lo <= r['a'] < crt_hi:
        return 'crt'
    if r.get('data_like'):
        return 'data'
    return 'game'


def pct(n, total):
    return 100.0 * n / total if total else 0.0


def fmt(n):
    return '{:,}'.format(n)


def print_table(title, buckets, total_n, total_b):
    print('\n== %s ==' % title)
    print('%-13s %6s %11s %7s %7s' % ('', 'funcs', 'bytes', 'funcs%', 'bytes%'))
    for key in sorted(buckets, key=lambda k: -buckets[k][1]):
        n, b = buckets[key]
        if not n:
            continue
        print('%-13s %6s %11s %7s %7s' % (
            key.ljust(13), str(n).rjust(6), fmt(b).rjust(11),
            ('%.1f%%' % pct(n, total_n)).rjust(7), ('%.1f%%' % pct(b, total_b)).rjust(7)))
    print('%-13s %6s %11s' % ('total', fmt(total_n), fmt(total_b)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('exe', nargs='?', help='the original exe (enables the machine-code analysis)')
    ap.add_argument('--functions', default=os.path.join(REPO, 'symbols', 'attt_functions.tsv'))
    ap.add_argument('--sym', action='append', default=[])
    ap.add_argument('--src', default=os.path.join(REPO, 'rebuild', 'src'))
    ap.add_argument('--auto', help='the auto-decompiled directory (rebuild/build.py --auto)')
    ap.add_argument('--replace', default=os.path.join(REPO, 'rebuild', 'build', 'work_attt', 'replace.txt'),
                    help='replace.txt of a build (default: %(default)s)')
    ap.add_argument('--lua-range', default='401000-420600', metavar='LO-HI',
                    help='the Lua 5.1 library addresses (default: %(default)s)')
    ap.add_argument('--crt-range', default='5E0000-607000', metavar='LO-HI',
                    help='compiler/linker-generated code at the end of .text (default: %(default)s)')
    ap.add_argument('--top', type=int, default=40, help='rows in the largest-untouched table')
    ap.add_argument('--csv', help='write every function as address,size,origin,nature,...')
    ap.add_argument('--json', help='write the tables and every function as JSON')
    a = ap.parse_args()
    lua_lo, lua_hi = (int(x, 16) for x in a.lua_range.split('-'))
    crt_lo, crt_hi = (int(x, 16) for x in a.crt_range.split('-'))
    syms_paths = a.sym or [os.path.join(REPO, 'symbols', n) for n in
                           ('attt.sym', 'attt_manual.sym', 'attt_ctors.sym', 'attt_singletons.sym')]

    rows = read_functions(a.functions)
    syms = read_syms(syms_paths)
    markers = scan_markers(a.src) if os.path.isdir(a.src) else {}
    hand = set().union(*markers.values()) if markers else set()
    auto_src = scan_markers(a.auto).get('', set()) if a.auto and os.path.isdir(a.auto) else set()
    replace = read_replace(a.replace)
    replaced = set(replace) | hand | auto_src
    statuses = read_statuses(a.auto)
    auto_status_known = bool(statuses)

    unit_of = {}
    for unit, addrs in markers.items():
        for addr in addrs:
            unit_of.setdefault(addr, unit)

    for r in rows:
        addr = r['a']
        unit = unit_of.get(addr)
        if unit in ('engine', 'lua51'):
            r['origin'] = unit
        elif addr in hand:
            r['origin'] = 'fixed'
        elif addr in replace or addr in auto_src:
            r['origin'] = 'auto'
        else:
            r['origin'] = 'untouched'
        r['replaced'] = addr in replaced
        r['status'] = statuses.get(addr, '')
        r['name'], r['tag'] = syms.get(addr, ('', ''))

    if a.exe:
        analyze_machine(a.exe, rows, lua_lo, lua_hi, crt_lo, crt_hi)

    for r in rows:
        r['nature'] = nature_of(r, syms, lua_lo, lua_hi, crt_lo, crt_hi)
        r['template'] = (r['nature'] in BACKLOG_NATURES and r.get('msvc_calls', 0) >= 2
                         and r.get('game_calls', 0) == 0 and r['size'] >= 32)

    total_n, total_b = len(rows), sum(r['size'] for r in rows)
    origin = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        o = origin[r['origin']]
        o[0] += 1
        o[1] += r['size']
    nature = collections.defaultdict(lambda: [0, 0])
    nature_n = collections.defaultdict(lambda: [0, 0])
    matrix = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        nature[r['nature']][0] += 1
        nature[r['nature']][1] += r['size']
        if r['origin'] == 'untouched':
            nature_n[r['nature']][0] += 1
            nature_n[r['nature']][1] += r['size']
        matrix[(r['nature'], r['origin'])][0] += 1
        matrix[(r['nature'], r['origin'])][1] += r['size']

    print('inventory: %s functions, %s bytes of .text (function sizes include the alignment up to the next entry)'
          % (fmt(total_n), fmt(total_b)))
    if not a.exe:
        print('(no EXE given: thunk/funclet/SEH/data detection and inbound call counts are off)')

    print_table('origin (who wrote the current code)', origin, total_n, total_b)

    print('\n== nature (what the code is) ==')
    print('%-13s %6s %10s %10s %10s %10s' % ('', 'funcs', 'bytes', 'replaced', 'untouched', 'unt.bytes'))
    for nat in NATURES:
        n, b = nature.get(nat, (0, 0))
        if not n:
            continue
        nn, nb = nature_n.get(nat, (0, 0))
        print('%-13s %6s %10s %10s %10s %10s' % (nat, str(n).rjust(6), fmt(b).rjust(10),
                                                 fmt(n - nn).rjust(10), fmt(nn).rjust(10), fmt(nb).rjust(10)))
    print('%-13s %6s %10s %10s %10s %10s' % ('total', str(total_n).rjust(6), fmt(total_b).rjust(10),
                                             fmt(total_n - sum(v[0] for v in nature_n.values())).rjust(10),
                                             fmt(sum(v[0] for v in nature_n.values())).rjust(10),
                                             fmt(sum(v[1] for v in nature_n.values())).rjust(10)))

    print('\n== origin x nature (functions / bytes) ==')
    print('%-13s %14s %14s %14s %14s' % ('nature', 'engine', 'lua51', 'fixed', 'auto'))
    for nat in NATURES:
        cells = []
        for org in ('engine', 'lua51', 'fixed', 'auto'):
            n, b = matrix.get((nat, org), (0, 0))
            cells.append(('%d/%s' % (n, fmt(b))) if n else '')
        if any(cells):
            print('%-13s %14s %14s %14s %14s' % ((nat,) + tuple(cells)))

    backlog = [r for r in rows if r['origin'] == 'untouched' and r['nature'] in BACKLOG_NATURES]
    backlog_b = sum(r['size'] for r in backlog)
    print('\n== untouched game code (the hand-translation backlog) ==')
    print('%s functions, %s bytes' % (fmt(len(backlog)), fmt(backlog_b)))
    if backlog:
        print('by the auto decompiler:')
        by_status = collections.Counter()
        status_b = collections.Counter()
        for r in backlog:
            key = r['status'] or ('not attempted (no row in the auto run)' if auto_status_known
                                  else 'not attempted (no auto run given)')
            by_status[key] += 1
            status_b[key] += r['size']
        for key, n in by_status.most_common():
            print('  %-72s %5d %10s B' % (key, n, fmt(status_b[key])))
        templates = [r for r in backlog if r.get('template')]
        if templates:
            print('  of them %d functions (%s B) look like MSVC/STL template instantiations (>=2 MSVCP8/MSVCR8 '
                  'calls, no call into the game)' % (len(templates), fmt(sum(r['size'] for r in templates))))
        print('\nlargest %d:' % a.top)
        print('%-10s %6s %-11s %-40s %-38s %5s %s' % ('address', 'bytes', 'nature', 'name', 'auto status', 'in', 'flags'))
        for r in sorted(backlog, key=lambda r: -r['size'])[:a.top]:
            flags = []
            if r.get('seh'):
                flags.append('seh')
            if r.get('template'):
                flags.append('template')
            print('%-10s %6d %-11s %-40s %-38s %5d %s' % (
                '%08X' % r['a'], r['size'], r['nature'], (r['name'] or r['tag'] or '-')[:40],
                r['status'][:38] or '-', r.get('inbound', 0), ','.join(flags)))

    lua = [r for r in rows if r['nature'] == 'lua-lib']
    print('\n== Lua 5.1 library ==')
    print('%s functions, %s bytes; replaced: %d, untouched: %d (%s B) -- build the library from its sources'
          % (fmt(len(lua)), fmt(sum(r['size'] for r in lua)),
             sum(1 for r in lua if r['replaced']), sum(1 for r in lua if not r['replaced']),
             fmt(sum(r['size'] for r in lua if not r['replaced']))))

    glue = [r for r in rows if r['nature'] in ('thunk', 'funclet', 'crt')]
    print('\n== compiler/linker glue (keep the original bytes) ==')
    for nat in ('thunk', 'funclet', 'crt'):
        g = [r for r in glue if r['nature'] == nat]
        print('%-8s %s functions, %s bytes (untouched: %d)' % (nat, fmt(len(g)), fmt(sum(r['size'] for r in g)),
                                                              sum(1 for r in g if r['origin'] == 'untouched')))
    data = [r for r in rows if r['nature'] == 'data']
    if data:
        print('false function rows: %s (%s B) -- AddMissingFunctions.java entries after a 0xCC byte inside the EH '
              'thunk tables; not functions, and the row before each one ends there' % (fmt(len(data)),
                                                                                      fmt(sum(r['size'] for r in data))))

    if a.csv:
        with open(a.csv, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f, delimiter='\t')
            w.writerow(['address', 'size', 'origin', 'nature', 'name', 'tag', 'auto_status', 'inbound',
                        'imports', 'flags'])
            for r in rows:
                flags = [x for x in ('seh', 'template', 'replaced') if r.get(x)]
                w.writerow(['%08X' % r['a'], r['size'], r['origin'], r['nature'], r['name'], r['tag'],
                            r['status'], r.get('inbound', 0),
                            ';'.join(sorted(r.get('imports', {}))) if r.get('imports') else '', ','.join(flags)])
        print('\nwrote %s' % a.csv)
    if a.json:
        detail = []
        for r in rows:
            detail.append({k: (('%08X' % v) if k == 'a' else (dict(v) if isinstance(v, collections.Counter)
                                                               else v))
                           for k, v in r.items()})
        out = {
            'inventory': {'functions': total_n, 'bytes': total_b},
            'origins': {k: {'functions': v[0], 'bytes': v[1]} for k, v in origin.items()},
            'natures': {k: {'functions': v[0], 'bytes': v[1]} for k, v in nature.items()},
            'untouched_natures': {k: {'functions': v[0], 'bytes': v[1]} for k, v in nature_n.items()},
            'functions': detail,
        }
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=1)
        print('wrote %s' % a.json)


if __name__ == '__main__':
    main()
