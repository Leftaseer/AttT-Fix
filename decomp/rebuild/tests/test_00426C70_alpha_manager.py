"""The alpha control manager:
0x00426C40 (ECX,EAX, ret 4): sets the +0x49 flag to the argument's low byte, reports the argument to every control
in the +0x5C list through the +0x54 virtual of the control's +0x54 part and returns the last result (EAX when the
list is empty).
0x00426C70 (ECX, ret 4): runs the +4 virtual of the current highlight while the +0x66C pick entries are zero, then
hit-tests every control at the +0x64 position; the new highlight gets +8, the released one +0xC."""
import struct

from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _hook(h, target, code):
    stub = _stub(h, code)
    _patch(h, target, b'\xE9' + struct.pack('<i', stub - (target + 5)))
    return stub


def _restore(h):
    for address, code in saved.items():
        h.uc.mem_write(address, code)
        h.uc.ctl_remove_cache(address, address + len(code))
    saved.clear()


def test_00426C40(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x80, bytes(0x80))
        v = _stub(h, b'\x89\x0D' + _dword(log + 4) + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + 8)
                  + b'\xFF\x05' + _dword(log) + b'\xB8' + _dword(0x55550000) + b'\xC2\x04\x00')
        w = _stub(h, b'\x89\x0D' + _dword(log + 0x10) + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + 0x14)
                  + b'\xFF\x05' + _dword(log + 0x0c) + b'\xB8' + _dword(0x66660000) + b'\xC2\x04\x00')
        vt1 = h.alloc(0x58, bytes(0x58))
        vt2 = h.alloc(0x58, bytes(0x58))
        h.uc.mem_write(vt1 + 0x54, _dword(v))
        h.uc.mem_write(vt2 + 0x54, _dword(w))
        o1 = h.alloc(0x60, bytes(0x60))
        o2 = h.alloc(0x60, bytes(0x60))
        h.uc.mem_write(o1 + 0x54, _dword(vt1))
        h.uc.mem_write(o2 + 0x54, _dword(vt2))
        obj = h.alloc(0x70, b'\xEE' * 0x70)
        sentinel = h.alloc(12, bytes(12))
        n1 = h.alloc(12, bytes(12))
        n2 = h.alloc(12, bytes(12))
        h.uc.mem_write(obj + 0x5c, _dword(sentinel))

        def setup(empty):
            h.uc.mem_write(log, bytes(0x80))
            h.uc.mem_write(obj, b'\xEE' * 0x70)
            h.uc.mem_write(obj + 0x5c, _dword(sentinel))
            h.uc.mem_write(sentinel, _dword(sentinel if empty else n1)
                           + _dword(sentinel if empty else n2) + bytes(4))
            h.uc.mem_write(n1, _dword(n2 if not empty else n1) + _dword(sentinel) + _dword(o1))
            h.uc.mem_write(n2, _dword(sentinel) + _dword(n1) + _dword(o2))

        for empty in (0, 1):
            setup(empty)
            diffs = h.compare(0x00426C40, args=[0x1234], regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0xA0B0C0D0},
                              ret='eax')
            if diffs:
                return ['empty %s: %s' % (bool(empty), d) for d in diffs]
            setup(empty)
            res = h.call(0x00426C40, args=[0x1234], regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0xA0B0C0D0})
            if res['fault']:
                return ['empty %s: replacement faulted: %s' % (bool(empty), res['fault'])]
            if h.uc.mem_read(obj + 0x49, 1)[0] != 0x34:
                return ['empty %s: the flag is %02X' % (bool(empty), h.uc.mem_read(obj + 0x49, 1)[0])]
            if empty:
                if res['eax'] != 0xA0B0C0D0 or _u32(h, log):
                    return ['empty list: returned %08X and the virtual ran' % res['eax']]
                continue
            if _u32(h, log) != 1 or _u32(h, log + 4) != o1 + 0x54 or _u32(h, log + 8) != 0x1234:
                return ['node 1: the +0x54 virtual got (%08X, %08X)' % (_u32(h, log + 4), _u32(h, log + 8))]
            if _u32(h, log + 0x0c) != 1 or _u32(h, log + 0x10) != o2 + 0x54 or _u32(h, log + 0x14) != 0x1234:
                return ['node 2: the +0x54 virtual got (%08X, %08X)' % (_u32(h, log + 0x10), _u32(h, log + 0x14))]
            if res['eax'] != 0x66660000:
                return ['returned %08X instead of the last virtual result' % res['eax']]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0


L_CTX = 0x60
L_EAX = 0x30
L_X = 0x34
L_Y = 0x38
L_CNT = 0x3c
L_HITS = 0x40
L_OBJ = 0x5c
L_SEQ = 0x80
L_CUR = 0xC0
KIND4, KIND8, KIND12 = 4, 8, 12


def _virtual_stub(h, seq_cursor, kind, retval):
    # record [object, kind] in the sequence and return retval
    return _stub(h, b'\xA1' + _dword(seq_cursor) + b'\x89\x08' + b'\xC7\x40\x04' + _dword(kind)
                 + b'\x83\xC0\x08' + b'\xA3' + _dword(seq_cursor) + b'\xB8' + _dword(retval) + b'\xC3')


def _FBITS(x):
    return struct.unpack('<I', struct.pack('<f', x))[0]


def test_00426C70(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x100, bytes(0x100))
        _hook(h, 0x00426B20,
              b'\x89\x0D' + _dword(log + L_OBJ) + b'\xA1' + _dword(log + L_OBJ)
              + b'\xFF\x05' + _dword(log + L_CNT) + b'\x8B\x0D' + _dword(log + L_CNT)
              + b'\x89\x04\x8D' + _dword(log + L_CTX)
              + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + L_X)
              + b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + L_Y)
              + b'\x8B\x0D' + _dword(log + L_CNT)
              + b'\x8B\x04\x8D' + _dword(log + L_HITS) + b'\xC2\x08\x00')

        def control(slotret):
            vt = h.alloc(0x18, bytes(0x18))
            obj = h.alloc(0x60, _dword(vt) + bytes(0x5c))
            for slot, kind in ((4, KIND4), (8, KIND8), (0xc, KIND12)):
                h.uc.mem_write(vt + slot, _dword(_virtual_stub(h, log + L_CUR, kind, slotret + kind)))
            return obj

        prev = control(0x1000)
        a = control(0x2000)
        b = control(0x3000)
        pos = h.alloc(0x210, bytes(0x210))
        h.uc.mem_write(pos + 0x204, struct.pack('<f', 12.5))
        h.uc.mem_write(pos + 0x208, struct.pack('<f', -3.25))
        table = h.alloc(0x680, bytes(0x680))
        skip = h.alloc(8, bytes(8))
        h.uc.mem_write(table + 0x66c, _dword(skip))
        obj = h.alloc(0x70, b'\xEE' * 0x70)
        sentinel = h.alloc(12, bytes(12))
        h.uc.mem_write(obj + 0x5c, _dword(sentinel))
        h.uc.mem_write(obj + 0x64, _dword(pos))
        h.uc.mem_write(obj + 0x68, _dword(table))

        def setup(nodes, hits, skipvals, current):
            h.uc.mem_write(log, bytes(0x100))
            h.uc.mem_write(log + L_CUR, _dword(log + L_SEQ))
            for i, hit in enumerate(hits):
                h.uc.mem_write(log + L_HITS + 4 + 4 * i, _dword(hit))
            h.uc.mem_write(obj + 0x6c, _dword(current) if current else bytes(4))
            n_ = len(nodes)
            for i, (node, ctl) in enumerate(nodes):
                nxt = nodes[i + 1][0] if i + 1 < n_ else sentinel
                prv = nodes[i - 1][0] if i else sentinel
                h.uc.mem_write(node, _dword(nxt) + _dword(prv) + _dword(ctl))
            h.uc.mem_write(sentinel, _dword(nodes[0][0] if n_ else sentinel)
                           + _dword(nodes[-1][0] if n_ else sentinel) + bytes(4))
            h.uc.mem_write(skip, b''.join(_dword(v) for v in skipvals))
            h.uc.mem_write(table + 0x670, _dword(len(skipvals)))

        na = h.alloc(12, bytes(12))
        nb = h.alloc(12, bytes(12))
        na2 = h.alloc(12, bytes(12))

        cases = [
            ('B hit', [(na, a), (nb, b)], [0, 1], [1, 0], prev, 0x3008,
             [(prev, KIND4), (prev, KIND12), (b, KIND8)], [a, b]),
            ('both miss', [(na, a), (nb, b)], [0, 0], [1, 0], prev, 0x100c,
             [(prev, KIND4), (prev, KIND12)], [a, b]),
            ('A then B hit', [(na, a), (nb, b)], [1, 1], [1, 0], prev, 0x3008,
             [(prev, KIND4), (prev, KIND12), (a, KIND8), (a, KIND12), (b, KIND8)], [a, b]),
            ('A twice', [(na, a), (na2, a)], [1, 1], [1, 0], prev, 0x00000001,
             [(prev, KIND4), (prev, KIND12), (a, KIND8)], [a, a]),
            ('no highlight miss', [(na, a)], [0], [], 0, 0x00000000,
             [], [a]),
        ]

        for name, nodes, hits, skipvals, current, retval, calls, tested in cases:
            setup(nodes, hits, skipvals, current)
            diffs = h.compare(0x00426C70, args=[0], regs={UC_X86_REG_ECX: obj}, ret='eax')
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            setup(nodes, hits, skipvals, current)
            res = h.call(0x00426C70, args=[0], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            if res['eax'] != retval:
                return ['%s: returned %08X, expected %08X' % (name, res['eax'], retval)]
            for k, (want_obj, want_kind) in enumerate(calls):
                got = (_u32(h, log + L_SEQ + 8 * k), _u32(h, log + L_SEQ + 8 * k + 4))
                if got != (want_obj, want_kind):
                    return ['%s: virtual %d was (%08X, %d), expected (%08X, %d)'
                            % ((name, k) + got + (want_obj, want_kind))]
            if _u32(h, log + L_CUR) != log + L_SEQ + 8 * len(calls):
                return ['%s: %d virtual calls, expected %d'
                        % (name, (_u32(h, log + L_CUR) - log - L_SEQ) // 8, len(calls))]
            if _u32(h, log + L_CNT) != len(tested):
                return ['%s: 0x426B20 ran %d times' % (name, _u32(h, log + L_CNT))]
            for k, o in enumerate(tested):
                if _u32(h, log + L_CTX + 4 * (k + 1)) != o:
                    return ['%s: hit test %d got control %08X'
                            % (name, k, _u32(h, log + L_CTX + 4 * (k + 1)))]
            if _u32(h, log + L_X) != _FBITS(12.5) or _u32(h, log + L_Y) != _FBITS(-3.25):
                return ['%s: the hit test got (%08X, %08X)' % (name, _u32(h, log + L_X), _u32(h, log + L_Y))]
            want_current = 0 if name in ('both miss', 'no highlight miss') else (a if name == 'A twice' else b)
            if _u32(h, obj + 0x6c) != want_current:
                return ['%s: the highlight is %08X' % (name, _u32(h, obj + 0x6c))]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0
