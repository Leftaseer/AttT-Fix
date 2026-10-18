#!/usr/bin/env python3
# dx.py EXE ADDR [N] : disassemble N bytes with string/annotation hints
import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__))); from pe import PE
import capstone
p = PE(sys.argv[1]); a = int(sys.argv[2], 16); n = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0x100
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for i in md.disasm(p.read(a, n), a):
    x = ''
    for t in i.op_str.replace(',', ' ').replace('[', ' ').replace(']', ' ').split():
        if t.startswith('0x'):
            v = int(t, 16)
            if v in p.imports: x += ' ; %s!%s' % p.imports[v]
            else:
                s = p.cstr(v, 80)
                if s and len(s) > 1: x += ' ; "%s"' % s
    print('%08X  %-7s %s%s' % (i.address, i.mnemonic, i.op_str, x))
