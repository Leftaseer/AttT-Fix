# Minimal PE helper: sections, VA<->offset, relocations, strings.
import pefile, struct, functools
class PE:
    def __init__(s, path):
        s.pe = pefile.PE(path, fast_load=False)
        s.data = open(path, 'rb').read()
        s.base = s.pe.OPTIONAL_HEADER.ImageBase
        s.secs = [(x.Name.rstrip(b'\0').decode(), s.base + x.VirtualAddress, x.Misc_VirtualSize, x.PointerToRawData, x.SizeOfRawData) for x in s.pe.sections]
        s.relocs = []
        if hasattr(s.pe, 'DIRECTORY_ENTRY_BASERELOC'):
            for b in s.pe.DIRECTORY_ENTRY_BASERELOC:
                for e in b.entries:
                    if e.type == 3: s.relocs.append(s.base + e.rva)
        s.relocs.sort(); s.relocset = set(s.relocs)
        s.imports = {}
        for e in s.pe.DIRECTORY_ENTRY_IMPORT:
            for i in e.imports:
                s.imports[i.address] = (e.dll.decode(), i.name.decode() if i.name else 'ord%d' % i.ordinal)
    def sec(s, va):
        for n, v, sz, o, rs in s.secs:
            if v <= va < v + max(sz, rs): return n
    def off(s, va):
        for n, v, sz, o, rs in s.secs:
            if v <= va < v + rs: return o + va - v
        return None
    def read(s, va, n):
        o = s.off(va)
        return None if o is None else s.data[o:o+n]
    def u32(s, va):
        b = s.read(va, 4); return struct.unpack('<I', b)[0] if b and len(b) == 4 else None
    def cstr(s, va, maxn=512):
        b = s.read(va, maxn)
        if not b: return None
        i = b.find(b'\0')
        if i <= 0: return None
        t = b[:i]
        if all(32 <= c < 127 or c >= 0xC0 or c in (9, 10, 13) for c in t):
            return t.decode('cp1251')
        return None
    def text_range(s):
        for n, v, sz, o, rs in s.secs:
            if n == '.text': return v, v + sz
