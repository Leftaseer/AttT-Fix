#!/usr/bin/env python3
"""exe2obj: turn a PE32 image with complete base relocations into a relinkable COFF object.

Every absolute address in the image is listed in .reloc, so each section can become an object
section whose absolute pointers are relocations against section symbols.  Relative branches stay
valid because each original section is kept as one contiguous block.  Imported functions become
references to __imp_ symbols of import libraries generated from the import table.

Usage: exe2obj.py EXE OUTDIR [--syms FILE] [--replace FILE]
  --syms     "ADDR NAME" lines: public symbols defined at those addresses (for new code to use)
  --replace  "ADDR NEWNAME" lines: the function at ADDR is replaced by external NEWNAME:
             a jmp to NEWNAME is placed at ADDR; pointers to ADDR stay (the function keeps one address)
             (--toggle: a jmp through a slot that the start-up code of the build can point back at the old code).
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
    ap.add_argument('--toggle', action='store_true', help='jmps through slots that rebuild/toggle.c can switch off '
                    'at start-up (decomp_toggle_table)')
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
        # pointers to replaced functions keep the old address (its entry jumps to the new code): a function has
        # one address for every comparison.  Redirected, the original destructor of 0x584DB0's objects removed a
        # mouse listener by the new address while the generated constructor had added it by the old one, and the
        # listener outlived its object (army screen drag and drop).
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

    # replaced functions: jmp NEW at the old entry.  --toggle: jmp to a stub 'jmp [slot]', the slot (data) holding
    # NEW, or for a replacement switched off at start-up (rebuild/toggle.c) the old entry's own first instructions
    # copied out (relative branches re-aimed, absolute addresses relocated) and a jmp back after them: no code is
    # written at run time.  An entry whose first bytes are jumped into from elsewhere stays plainly replaced.
    repl_jmp = repl
    if a.toggle:
        import capstone
        from capstone import x86
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        md.detail = True
        relocset = set(relocs)
        ti_ = find_sec(next(va for va in repl))
        text = secs[ti_]
        orig_text = bytes(raw[pe.get_offset_from_rva(text[1] - base):pe.get_offset_from_rva(text[1] - base) + text[2]])
        # targets of every direct branch in .text (linear sweep), to see which entries are jumped into
        inner = set()
        off = 0
        while off < len(orig_text):
            last = None
            for i in md.disasm(orig_text[off:], text[1] + off):
                last = i
                if (i.mnemonic.startswith('j') or i.mnemonic.startswith('loop')) and i.operands and \
                        i.operands[0].type == x86.X86_OP_IMM:
                    inner.add(i.operands[0].imm)
            off = (last.address + last.size - text[1] + 1) if last else off + 1

        def abs_target(tgt):
            """(stored value, symbol) of an absolute address in copied code, as the relocation loop does it"""
            if tgt in iat:
                return 0, sym(iat[tgt])
            t2 = find_sec(tgt)
            if t2 is None:
                return tgt - base, imagebase_sym
            return tgt - secs[t2][1], t2

        stubs, srel = bytearray(), []
        tab, trel = bytearray(struct.pack('<I', len(repl))), []
        slots, lrel = bytearray(), []
        items = sorted(repl.items())
        plain = {}
        n_tr = 0
        for k, (va, newname) in enumerate(items):
            # trampoline: whole instructions covering the 5 bytes of the jmp
            code = orig_text[va - text[1]:va - text[1] + 32]
            tr, trr, cover, ok = bytearray(), [], 0, True
            for i in md.disasm(code, va):
                if cover >= 5:
                    break
                if any(t in inner for t in range(va + 1, va + cover + i.size)):
                    ok = False
                op = i.operands[0] if i.operands else None
                rel_tgt = op.imm if op is not None and op.type == x86.X86_OP_IMM and \
                    (i.mnemonic in ('call', 'jmp') or i.mnemonic.startswith('j')) and i.mnemonic not in ('jecxz', 'jcxz') else None
                if i.mnemonic.startswith('loop') or i.mnemonic in ('jecxz', 'jcxz'):
                    ok = False
                if rel_tgt is not None:
                    ts = find_sec(rel_tgt)
                    if ts is None:
                        ok = False
                        break
                    if i.mnemonic == 'call':
                        tr += b'\xE8'
                    elif i.mnemonic == 'jmp':
                        tr += b'\xE9'
                    else:
                        cc = i.bytes[0] if i.bytes[0] != 0x0F else i.bytes[1] - 0x10
                        tr += bytes([0x0F, (cc & 0x0F) | 0x80])
                    trr.append((len(tr), ts, IMAGE_REL_I386_REL32))
                    tr += struct.pack('<I', rel_tgt - secs[ts][1])
                else:
                    b = bytearray(i.bytes)
                    for p_ in range(i.size - 3):
                        if i.address + p_ in relocset:
                            v, sy = abs_target(struct.unpack_from('<I', b, p_)[0])
                            struct.pack_into('<I', b, p_, v)
                            trr.append((len(tr) + p_, sy, IMAGE_REL_I386_DIR32))
                    tr += b
                cover += i.size
            if cover < 5:
                ok = False
            if not ok:
                plain[va] = newname
                tab += struct.pack('<II', va, 0)     # not switchable (rebuild/toggle.c leaves it on)
                slots += struct.pack('<I', 0)
                continue
            # the jmp back after the copied instructions
            tr += b'\xE9'
            trr.append((len(tr), ti_, IMAGE_REL_I386_REL32))
            tr += struct.pack('<I', va + cover - text[1])
            tr_off = len(stubs)
            stubs += tr
            srel += [(tr_off + o, sy, t) for o, sy, t in trr]
            while len(stubs) % 4:
                stubs += b'\xCC'
            # the stub the entry jumps to: jmp [slot]
            st_off = len(stubs)
            stubs += b'\xFF\x25'
            srel.append((len(stubs), 'SLOTS', IMAGE_REL_I386_DIR32))
            stubs += struct.pack('<I', 4 * k)
            stubs += b'\xCC\xCC'
            # slot: the new function (on) until toggle.c puts the trampoline there
            lrel.append((len(slots), sym(cname(newname)), IMAGE_REL_I386_DIR32))
            slots += struct.pack('<I', 0)
            # table: original address, trampoline
            trel.append((len(tab), ti_, IMAGE_REL_I386_DIR32))
            tab += struct.pack('<I', va - text[1])
            trel.append((len(tab), 'STUBS', IMAGE_REL_I386_DIR32))
            tab += struct.pack('<I', tr_off)
            # the entry: jmp stub
            s_ = text
            o_ = va - s_[1]
            s_[3][o_] = 0xE9
            struct.pack_into('<I', s_[3], o_ + 1, st_off)
            s_[4] = [x for x in s_[4] if not (o_ < x[0] + 4 and x[0] < o_ + 5)]
            s_[4].append((o_ + 1, 'STUBS', IMAGE_REL_I386_REL32))
            n_tr += 1
        SCN['.ntext'] = 0x60000020
        secs.append(['.ntext', 0xF0000000, len(stubs), stubs, srel])
        stub_sym = sym('$toggle_stubs', 0, len(secs), 3)
        secs.append(['.ndata', 0xF1000000, len(tab) + len(slots), tab + slots,
                     trel + [(len(tab) + o, sy, t) for o, sy, t in lrel]])
        data_sec = len(secs)
        slot_sym = sym('$toggle_slots', len(tab), data_sec, 3)
        sym('_decomp_toggle_table', 0, data_sec, 2)
        for s_ in secs:
            s_[4] = [(o, stub_sym if sy == 'STUBS' else slot_sym if sy == 'SLOTS' else sy, t) for o, sy, t in s_[4]]
        repl_jmp = plain
        print('toggle: %d switchable, %d always on' % (n_tr, len(plain)))
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
