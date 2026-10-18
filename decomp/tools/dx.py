#!/usr/bin/env python3
# dx.py EXE ADDR [N|func] [--syms FILE.sym]: disassemble with names of imports, strings and symbols.
# N may be 'f' to disassemble up to the next function start listed in symbols/<game>_functions.tsv.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import PE
import capstone
args = [a for a in sys.argv[1:] if not a.startswith('--')]
p = PE(args[0]); a = int(args[1], 16)
syms = {}
if '--syms' in sys.argv:
    for l in open(sys.argv[sys.argv.index('--syms') + 1], encoding='utf-8'):
        if l[0] in '#S' or not l.strip(): continue
        b = l.split('#')[0].split(None, 2); syms[int(b[0], 16)] = b[2].strip()
n = 0x100
if len(args) > 2:
    if args[2] == 'f':
        here = os.path.dirname(os.path.abspath(__file__))
        game = 'valk' if p.pe.FILE_HEADER.TimeDateStamp == 0x4883FB4F else 'attt'
        starts = sorted(int(l.split('\t')[0], 16) for l in open(os.path.join(here, '..', 'symbols', game + '_functions.tsv')) if l[0] != '#')
        nxt = [s for s in starts if s > a]
        n = (nxt[0] - a) if nxt else 0x100
    else:
        n = int(args[2], 0)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for i in md.disasm(p.read(a, n), a):
    x = ''
    for t in i.op_str.replace(',', ' ').replace('[', ' ').replace(']', ' ').replace('+', ' ').replace('-', ' ').split():
        if t.startswith('0x'):
            v = int(t, 16)
            if v in p.imports: x += ' ; %s!%s' % p.imports[v]
            elif v in syms: x += ' ; ' + syms[v]
            else:
                s = p.cstr(v, 80)
                if s and len(s) > 1 and v > 0x10000: x += ' ; "%s"' % s
    if i.mnemonic == 'int3': break
    print('%08X  %-7s %s%s' % (i.address, i.mnemonic, i.op_str, x))
