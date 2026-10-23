#!/usr/bin/env python3
"""Calling convention and argument bytes of the C++ functions an exe imports (MSVCP80, MSVCR80), from their
decorated names (llvm-undname).  Ghidra types imports by their plain names and gave some MSVCP80 members the
prototypes of C functions of the same name (std::basic_ifstream::close as 'int close(int)', __cdecl), and it
does not see the hidden parameters: the address of a class returned by value, the most-derived flag of
constructors of classes with a virtual base.  ghidra/DecoratedImports.java makes the prototypes agree.

usage: cxximports.py EXE OUT.tsv      OUT: decorated name, convention, bytes of stack arguments (without this),
                                           'class' if a class is returned by value (its address is the first)"""
import os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import PE

# classes with a virtual base (std::basic_ios): their constructors take a last int
VBASE = re.compile(r'^std::basic_(i|o|io|if|of|f|istring|ostring|string)stream<')


def split_top(s):
    out, depth, cur = [], 0, ''
    for ch in s:
        if ch in '<(':
            depth += 1
        elif ch in '>)':
            depth -= 1
        if ch == ',' and depth == 0:
            out.append(cur.strip())
            cur = ''
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


# classes the imports take by value, by size (std::string::operator[](_Size_type_nosscl) of the checked
# iterators: a size_t in a struct; 0x46D380 calls it)
BY_VALUE_SIZES = {'::_Size_type_nosscl': 4}


def arg_bytes(t):
    t = t.strip()
    if t in ('void', '...'):
        return 0
    if t.endswith(('*', '&')) or '(' in t:
        return 4
    if re.search(r'\b(__int64|double)\b', t) and 'long double' not in t:
        return 8
    if t == 'long double':
        return 8
    if re.match(r'^(class|struct|union) ', t):
        # a class by value: its size is not in the name, except for the few the C++ runtime passes
        for k, n in BY_VALUE_SIZES.items():
            if t.endswith(k):
                return n
        return None
    return 4                           # int, char, bool, enums, float: one stack slot


def parse(name):
    try:
        d = subprocess.run(['llvm-undname', name], capture_output=True, text=True).stdout.strip().splitlines()[-1]
    except Exception:
        return None
    m = re.search(r'\b(__cdecl|__stdcall|__thiscall|__fastcall)\s+(.*?)\((.*)\)\s*(const)?\s*$', d)
    if not m:
        return None
    cc, qual, params = m.group(1), m.group(2), m.group(3)
    head = d[:m.start(1)]
    ps = split_top(params)
    if ps == ['void']:
        ps = []
    n = 0
    for p in ps:
        if p == '...':
            return cc, None, ''
        b = arg_bytes(p)
        if b is None:
            return cc, None, ''
        n += b
    ret = re.sub(r'^(public|protected|private):\s*', '', head).replace('static ', '').replace('virtual ', '').strip()
    by_value = bool(re.match(r'^(class|struct|union) ', ret)) and not ret.endswith(('*', '&'))
    if by_value:
        n += 4
    # constructors (Class::Class) of classes with a virtual base
    parts, depth, cur = [], 0, ''
    for i, ch in enumerate(qual):
        depth += ch == '<'
        depth -= ch == '>'
        if depth == 0 and qual.startswith('::', i):
            parts.append(cur)
            cur = ''
        elif not (depth == 0 and i > 0 and qual.startswith('::', i - 1)):
            cur += ch
    parts.append(cur)
    owner = '::'.join(parts[:-1])
    if len(parts) > 1 and parts[-2].split('<')[0] == parts[-1].split('<')[0] and VBASE.match(owner):
        n += 4
    return cc, n, 'class' if by_value else ''


def main():
    pe = PE(sys.argv[1])
    rows = []
    for slot, (dll, name) in sorted(pe.imports.items()):
        if not name.startswith('?'):
            continue
        r = parse(name)
        if r is None or r[1] is None:
            continue
        rows.append('%s\t%s\t%d\t%s' % (name, r[0], r[1], r[2]))
    with open(sys.argv[2], 'w') as f:
        f.write('# decorated name\tconvention\tbytes of stack arguments (without this)\tclass returned by value'
                ' (tools/cxximports.py)\n')
        f.write('\n'.join(rows) + '\n')
    print('%d C++ imports' % len(rows))


if __name__ == '__main__':
    main()
