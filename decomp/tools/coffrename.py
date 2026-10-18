#!/usr/bin/env python3
"""Rename sections of a COFF object in place: .text* -> .ntext*, .rdata* -> .nrdata*, .data* -> .ndata*,
.bss* -> .nbss*.  The rebuilt exe then keeps the original .text/.rdata/.data at their original addresses and
places new code and data after them.  usage: coffrename.py OBJ..."""
import sys, struct
MAP = (('.text', '.ntext'), ('.rdata', '.nrdata'), ('.data', '.ndata'), ('.bss', '.nbss'))
def fix(path):
    b = bytearray(open(path, 'rb').read())
    mach, nsec, ts, symptr, nsym, opt, ch = struct.unpack_from('<HHIIIHH', b, 0)
    strtab = symptr + 18 * nsym
    strsize = struct.unpack_from('<I', b, strtab)[0]
    extra = bytearray()
    for i in range(nsec):
        h = 20 + opt + 40 * i
        raw = bytes(b[h:h + 8])
        if raw.startswith(b'/'):
            off = int(raw[1:].rstrip(b'\0'))
            e = b.index(b'\0', strtab + off)
            name = b[strtab + off:e].decode()
        else:
            name = raw.rstrip(b'\0').decode()
        new = name
        for a, n in MAP:
            if name == a or name.startswith(a + '$'):
                new = n + name[len(a):]
        if new == name:
            continue
        enc = new.encode()
        if len(enc) <= 8:
            b[h:h + 8] = enc.ljust(8, b'\0')
        else:
            off = strsize + len(extra)
            extra += enc + b'\0'
            b[h:h + 8] = ('/%d' % off).encode().ljust(8, b'\0')
    if extra:
        b = b[:strtab + strsize] + extra + b[strtab + strsize:]
        struct.pack_into('<I', b, strtab, strsize + len(extra))
    open(path, 'wb').write(b)
for p in sys.argv[1:]:
    fix(p)
