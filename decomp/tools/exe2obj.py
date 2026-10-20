#!/usr/bin/env python3
"""exe2obj: turn a PE32 image with complete base relocations into a relinkable COFF object.

Every absolute address in the image is listed in .reloc, so each section can become an object
section whose absolute pointers are relocations against section symbols.  Relative branches stay
valid because each original section is kept as one contiguous block.  Imported functions become
references to __imp_ symbols of import libraries generated from the import table.

Usage: exe2obj.py EXE OUTDIR [--syms FILE] [--replace FILE]
  --syms     "ADDR NAME" lines: public symbols defined at those addresses (for new code to use)
  --replace  "ADDR NEWNAME" lines: the function at ADDR is replaced by external NEWNAME:
             a jmp to NEWNAME is placed at ADDR and every pointer to ADDR is redirected
             (--toggle: neither, the start-up code of the build writes the jmps it is told to).
Outputs: orig.obj, imports/*.def, resources.res, link.rsp (lld-link options)
"""
import sys, os, struct, argparse, pefile

IMAGE_REL_I386_DIR32 = 6
IMAGE_REL_I386_REL32 = 0x14
SCN = {'.text': 0x60000020, '.rdata': 0x40000040, '.data': 0xC0000040, '.ndata': 0xC0000040}
ALIGN_4096 = 0x00D00000
NRELOC_OVFL = 0x01000000

def cname(n):
    """COFF symbol of a C name (leading underscore); decorated C++/fastcall names are kept as they are"""
    return n if n[0] in '?@' else '_' + n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('exe'); ap.add_argument('outdir')
    ap.add_argument('--syms'); ap.add_argument('--replace')
    ap.add_argument('--toggle', action='store_true', help='no jmps and no redirected pointers: the replacements go '
                    'into decomp_toggle_table (original address, new function) for rebuild/toggle.c to apply at start-up')
    a = ap.parse_args()
    pe = pefile.PE(a.exe)
    base = pe.OPTIONAL_HEADER.ImageBase
    raw = open(a.exe, 'rb').read()
    os.makedirs(a.outdir, exist_ok=True)

    secs = []  # name, va, vsize, bytes
    for s in pe.sections:
        n = s.Name.rstrip(b'\0').decode()
        if n not in SCN: continue
        size = s.Misc_VirtualSize     # not the raw size: the rest of the last page is free for linker thunks
        size = (size + 15) & ~15
        b = bytearray(raw[s.PointerToRawData:s.PointerToRawData + min(s.SizeOfRawData, size)])
        b += bytes(size - len(b))
        secs.append([n, base + s.VirtualAddress, size, b, []])
    first_va = min(s[1] for s in secs)

    def find_sec(va, prefer=None):
        for i, s in enumerate(secs):
            if s[1] <= va < s[1] + s[2]: return i
        for i, s in enumerate(secs):  # one-past-the-end pointers
            if va == s[1] + s[2]: return i
        return None

    # imports: IAT slot address -> (dll, symbol)
    iat = {}
    defs = {}
    for e in pe.DIRECTORY_ENTRY_IMPORT:
        dll = e.dll.decode()
        for imp in e.imports:
            if imp.name:
                nm = imp.name.decode()
                sym = '__imp_' + nm if nm.startswith('?') else '__imp__' + nm
                defs.setdefault(dll, []).append('%s == %s' % (nm, nm))
            else:
                nm = '%s_ord%d' % (dll.split('.')[0], imp.ordinal)
                sym = '__imp__' + nm
                defs.setdefault(dll, []).append('%s @%d NONAME' % (nm, imp.ordinal))
            iat[imp.address] = sym

    symtab = []  # (name, value, secnum(1-based or 0 undef or -1 abs), storage)
    symidx = {}
    def sym(name, value=0, secnum=0, storage=2):
        if name in symidx and secnum == 0: return symidx[name]
        symidx[name] = len(symtab); symtab.append((name, value, secnum, storage)); return symidx[name]
    for i, s in enumerate(secs):
        sym('$orig%s' % s[0].replace('.', '_'), 0, i + 1, 3)
    imagebase_sym = sym('___ImageBase')

    repl = {}
    if a.replace:
        for line in open(a.replace):
            p = line.split('#')[0].split()
            if len(p) >= 2: repl[int(p[0], 16)] = p[1]

    relocs = sorted(r for r in (base + e.rva for b in pe.DIRECTORY_ENTRY_BASERELOC for e in b.entries if e.type == 3))
    stats = {'iat': 0, 'sec': 0, 'hdr': 0, 'repl': 0, 'outside': 0}
    for r in relocs:
        si = find_sec(r)
        if si is None or r + 4 > secs[si][1] + secs[si][2]:
            continue  # reloc in a dropped section (.rsrc never has any)
        s = secs[si]; off = r - s[1]
        tgt = struct.unpack_from('<I', s[3], off)[0]
        if tgt in iat:
            struct.pack_into('<I', s[3], off, 0)
            s[4].append((off, sym(iat[tgt]), IMAGE_REL_I386_DIR32)); stats['iat'] += 1; continue
        if tgt in repl and not a.toggle:
            struct.pack_into('<I', s[3], off, 0)
            s[4].append((off, sym(cname(repl[tgt])), IMAGE_REL_I386_DIR32)); stats['repl'] += 1; continue
        ti = find_sec(tgt)
        if ti is None:
            if base <= tgt < first_va:
                struct.pack_into('<I', s[3], off, tgt - base)
                s[4].append((off, imagebase_sym, IMAGE_REL_I386_DIR32)); stats['hdr'] += 1
            else:
                stats['outside'] += 1
                print('warning: reloc at %08X points outside the image: %08X' % (r, tgt))
            continue
        struct.pack_into('<I', s[3], off, tgt - secs[ti][1])
        s[4].append((off, ti, IMAGE_REL_I386_DIR32)); stats['sec'] += 1

    # replaced functions: jmp NEW at the old entry, or (--toggle) a table of them for the start-up code
    if a.toggle:
        tab = bytearray(struct.pack('<I', len(repl)))
        rel = []
        for va, new in sorted(repl.items()):
            si = find_sec(va)
            rel.append((len(tab), si, IMAGE_REL_I386_DIR32))
            tab += struct.pack('<I', va - secs[si][1])
            rel.append((len(tab), sym(cname(new)), IMAGE_REL_I386_DIR32))
            tab += struct.pack('<I', 0)
        secs.append(['.ndata', 0xF0000000, len(tab), tab, rel])
        sym('_decomp_toggle_table', 0, len(secs), 2)
        repl_jmp = {}
    else:
        repl_jmp = repl
    for va, new in repl_jmp.items():
        si = find_sec(va); s = secs[si]; off = va - s[1]
        s[3][off] = 0xE9; struct.pack_into('<I', s[3], off + 1, 0)
        s[4] = [x for x in s[4] if not (off < x[0] + 4 and x[0] < off + 5)]
        s[4].append((off + 1, sym(cname(new)), IMAGE_REL_I386_REL32))

    # public symbols for new code
    if a.syms:
        seen = set()
        for line in open(a.syms):
            p = line.split('#')[0].split()
            if len(p) < 2: continue
            va = int(p[0], 16); nm = p[1]
            si = find_sec(va)
            if si is None or nm in seen: continue
            seen.add(nm)
            sym(cname(nm), va - secs[si][1], si + 1, 2)
    # section start symbols and the entry point
    for i, s in enumerate(secs):
        sym('__orig%s_start' % s[0].replace('.', '_'), 0, i + 1, 2)
    ep = base + pe.OPTIONAL_HEADER.AddressOfEntryPoint
    ei = find_sec(ep); sym('_orig_entry', ep - secs[ei][1], ei + 1, 2)

    write_coff(os.path.join(a.outdir, 'orig.obj'), secs, symtab)
    # import libraries
    os.makedirs(os.path.join(a.outdir, 'imports'), exist_ok=True)
    for dll, names in defs.items():
        with open(os.path.join(a.outdir, 'imports', dll.lower().replace('.dll', '') + '.def'), 'w') as f:
            f.write('LIBRARY %s\nEXPORTS\n' % dll)
            for n in names: f.write('  %s\n' % n)
    write_res(pe, os.path.join(a.outdir, 'resources.res'))
    oh = pe.OPTIONAL_HEADER
    with open(os.path.join(a.outdir, 'link.rsp'), 'w') as f:
        f.write('/machine:x86 /subsystem:windows,%d.%d /entry:orig_entry /base:0x%X /fixed:no /dynamicbase:no '
                '/nxcompat:no /safeseh:no /nodefaultlib /stack:0x%X,0x%X /heap:0x%X,0x%X /merge:.bss=.data\n'
                % (oh.MajorSubsystemVersion, oh.MinorSubsystemVersion, base,
                   oh.SizeOfStackReserve, oh.SizeOfStackCommit, oh.SizeOfHeapReserve, oh.SizeOfHeapCommit))
    print('relocations:', stats, ' replaced:', len(repl), ' symbols:', len(symtab))

def write_coff(path, secs, symtab):
    strtab = bytearray(4)
    def name8(n):
        b = n.encode()
        if len(b) <= 8: return b.ljust(8, b'\0')
        o = len(strtab); strtab.extend(b + b'\0'); return struct.pack('<II', 0, o)
    hdr_size = 20 + 40 * len(secs)
    out = bytearray(hdr_size)
    shdrs = []
    for n, va, size, data, rel in secs:
        rel.sort()
        ptr = len(out); out += data
        while len(out) % 4: out += b'\0'
        rptr = len(out); nrel = len(rel)
        flags = SCN[n] | ALIGN_4096
        if nrel > 0xFFFF:
            flags |= NRELOC_OVFL
            out += struct.pack('<IIH', nrel + 1, 0, 0); nrel_field = 0xFFFF
        else: nrel_field = nrel
        for off, si, typ in rel:
            out += struct.pack('<IIH', off, si, typ)
        shdrs.append(struct.pack('<8sIIIIIIHHI', n.encode().ljust(8, b'\0'), 0, 0, len(data), ptr,
                                 rptr if rel else 0, 0, nrel_field, 0, flags))
    symptr = len(out)
    for name, value, secnum, storage in symtab:
        out += name8(name) + struct.pack('<IhHBB', value, secnum, 0, storage, 0)
    struct.pack_into('<I', strtab, 0, len(strtab))
    out += strtab
    struct.pack_into('<HHIIIHH', out, 0, 0x14C, len(secs), 0, symptr, len(symtab), 0, 0)
    for i, h in enumerate(shdrs): out[20 + 40 * i:60 + 40 * i] = h
    open(path, 'wb').write(out)

def write_res(pe, path):
    out = bytearray(struct.pack('<IIHHHHIHHII', 0, 32, 0xFFFF, 0, 0xFFFF, 0, 0, 0, 0, 0, 0))
    def idfield(e):
        if e.name is not None:
            return (str(e.name) .encode('utf-16-le') + b'\0\0')
        return struct.pack('<HH', 0xFFFF, e.id)
    if not hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
        open(path, 'wb').write(out); return
    for t in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        for n in t.directory.entries:
            for l in n.directory.entries:
                d = l.data.struct
                data = pe.get_data(d.OffsetToData, d.Size)
                h = idfield(t) + idfield(n)
                while (8 + len(h)) % 4: h += b'\0'
                h += struct.pack('<IHHII', 0, 0x1030, l.id, 0, 0)
                out += struct.pack('<II', len(data), 8 + len(h)) + h + data
                while len(out) % 4: out += b'\0'
    open(path, 'wb').write(out)

if __name__ == '__main__':
    main()
