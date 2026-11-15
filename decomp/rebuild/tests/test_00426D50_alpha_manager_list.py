"""The alpha control manager's destructor and node removal:
0x00426D50 (ECX): vtable 0x0060819C, the +0x5C list emptied and freed, the +0x58 part destroyed, the control base.
0x00426DA0 (ECX, ret 4): unlinks and frees the node whose +8 payload equals the argument, decrementing +0x60."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

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


def _log_stub(h, log, off, ret=None, pop=0):
    code = b'\xFF\x05' + _dword(log + off) + b'\x89\x0D' + _dword(log + off + 4)
    if ret is not None:
        code += b'\xB8' + _dword(ret)
    if pop:
        code += b'\xC2' + struct.pack('<H', pop)
    else:
        code += b'\xC3'
    return _stub(h, code)


def test_00426D50(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x80, bytes(0x80))
        _hook(h, 0x005E3E9C, b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + 0x20)
              + b'\xFF\x05' + _dword(log + 0x24) + b'\xC3')
        _hook(h, 0x0044CFE0, b'\x89\x0D' + _dword(log) + b'\xFF\x05' + _dword(log + 4) + b'\xC3')
        _hook(h, 0x004AB940, b'\x89\x0D' + _dword(log + 8) + b'\xFF\x05' + _dword(log + 0x0c) + b'\xC3')

        nodes = [h.alloc(12, bytes(12)) for _ in range(3)]
        sentinel = h.alloc(12, bytes(12))
        obj = h.alloc(0x70, b'\xEE' * 0x70)

        def setup(n):
            h.uc.mem_write(log, bytes(0x80))
            h.uc.mem_write(obj, b'\xEE' * 0x70)
            h.uc.mem_write(obj + 0x5c, _dword(sentinel))
            h.uc.mem_write(obj + 0x60, _dword(n))
            for i in range(n):
                nxt = nodes[i + 1] if i + 1 < n else sentinel
                prv = nodes[i - 1] if i else sentinel
                h.uc.mem_write(nodes[i], _dword(nxt) + _dword(prv) + bytes(4))
            h.uc.mem_write(sentinel, _dword(nodes[0] if n else sentinel)
                           + _dword(nodes[n - 1] if n else sentinel) + bytes(4))

        for n in (3, 0):
            setup(n)
            diffs = h.compare(0x00426D50, regs={UC_X86_REG_ECX: obj}, ret=None)
            if diffs:
                return ['%d nodes: %s' % (n, d) for d in diffs]
            setup(n)
            res = h.call(0x00426D50, regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['%d nodes: replacement faulted: %s' % (n, res['fault'])]
            if _u32(h, obj) != 0x0060819C:
                return ['%d nodes: the vtable is %08X' % (n, _u32(h, obj))]
            if _u32(h, sentinel) != sentinel or _u32(h, sentinel + 4) != sentinel:
                return ['%d nodes: the sentinel links are %08X / %08X'
                        % (n, _u32(h, sentinel), _u32(h, sentinel + 4))]
            if _u32(h, obj + 0x60) != 0:
                return ['%d nodes: the count is %08X' % (n, _u32(h, obj + 0x60))]
            if _u32(h, log + 0x24) != n:
                return ['%d nodes: free ran %d times' % (n, _u32(h, log + 0x24))]
            if n:
                if _u32(h, log + 0x20) != nodes[n - 1]:
                    return ['%d nodes: the last free was %08X' % (n, _u32(h, log + 0x20))]
            if _u32(h, log + 4) != 1 or _u32(h, log) != obj + 0x58:
                return ['%d nodes: the +0x58 destructor got %08X' % (n, _u32(h, log))]
            if _u32(h, log + 0x0c) != 1 or _u32(h, log + 8) != obj:
                return ['%d nodes: the base destructor got %08X' % (n, _u32(h, log + 8))]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_00426DA0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x80, bytes(0x80))
        _hook(h, 0x005E3E9C, b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + 4)
              + b'\xFF\x05' + _dword(log) + b'\xC3')
        nodes = [h.alloc(12, bytes(12)) for _ in range(3)]
        sentinel = h.alloc(12, bytes(12))
        obj = h.alloc(0x70, b'\xEE' * 0x70)

        def build(entries, count):
            h.uc.mem_write(log, bytes(0x80))
            h.uc.mem_write(log + 4, bytes(0x7c))
            h.uc.mem_write(obj, b'\xEE' * 0x70)
            h.uc.mem_write(obj + 0x5c, _dword(sentinel))
            h.uc.mem_write(obj + 0x60, _dword(count))
            n_ = len(entries)
            h.uc.mem_write(sentinel, _dword(entries[0][0] if n_ else sentinel)
                           + _dword(entries[-1][0] if n_ else sentinel) + bytes(4))
            for i, (node, payload) in enumerate(entries):
                h.uc.mem_write(node, _dword(entries[i + 1][0] if i + 1 < n_ else sentinel)
                               + _dword(entries[i - 1][0] if i else sentinel) + _dword(payload))

        def check(name, entries, remove, count, removed_index):
            build(entries, count)
            diffs = h.compare(0x00426DA0, args=[remove], regs={UC_X86_REG_ECX: obj}, ret=None)
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            build(entries, count)
            res = h.call(0x00426DA0, args=[remove], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            left = [e for i, e in enumerate(entries) if i != removed_index]
            n_ = len(left)
            if _u32(h, sentinel) != (left[0][0] if n_ else sentinel):
                return ['%s: the first link is %08X' % (name, _u32(h, sentinel))]
            if _u32(h, sentinel + 4) != (left[-1][0] if n_ else sentinel):
                return ['%s: the last link is %08X' % (name, _u32(h, sentinel + 4))]
            for i, (node, payload) in enumerate(left):
                if _u32(h, node + 8) != payload:
                    return ['%s: node %d holds %08X' % (name, i, _u32(h, node + 8))]
                if _u32(h, node) != (left[i + 1][0] if i + 1 < n_ else sentinel):
                    return ['%s: node %d next is %08X' % (name, i, _u32(h, node))]
                if _u32(h, node + 4) != (left[i - 1][0] if i else sentinel):
                    return ['%s: node %d prev is %08X' % (name, i, _u32(h, node + 4))]
            if removed_index is None:
                if _u32(h, log) or _u32(h, obj + 0x60) != count:
                    return ['%s: free ran %d times, count %08X' % (name, _u32(h, log), _u32(h, obj + 0x60))]
            else:
                if _u32(h, log) != 1 or _u32(h, log + 4) != entries[removed_index][0]:
                    return ['%s: free got %08X' % (name, _u32(h, log + 4))]
                if _u32(h, obj + 0x60) != count - 1:
                    return ['%s: the count is %08X' % (name, _u32(h, obj + 0x60))]
            return None

        three = [(nodes[0], 0x7001), (nodes[1], 0x7002), (nodes[2], 0x7003)]
        for args in (
            ('remove second', three, 0x7002, 3, 1),
            ('remove first', three, 0x7001, 3, 0),
            ('remove last', three, 0x7003, 3, 2),
            ('remove only', [(nodes[0], 0x7001)], 0x7001, 1, 0),
            ('absent', three[:2], 0x7004, 2, None),
            ('empty', [], 0x7001, 0, None),
        ):
            err = check(*args)
            if err:
                return err
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0
