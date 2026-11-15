"""0x00426C00 (ECX): the alpha control manager's list clear: the +0x5C sentinel is relinked to itself, +0x60 is
zeroed and every former node is freed in list order."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def test_00426C00(h):
    heap0 = h.heap_ptr
    try:
        saved[0x005E3E9C] = bytes(h.uc.mem_read(0x005E3E9C, 5))
        log = h.alloc(0x40, bytes(0x40))
        stub = h.alloc(64, b'\x8B\x44\x24\x04' + b'\x8B\x0D' + _dword(log + 4) + b'\x89\x01\x83\xC1\x04'
                       + b'\x89\x0D' + _dword(log + 4) + b'\xFF\x05' + _dword(log) + b'\xC3')
        h.uc.ctl_remove_cache(stub, stub + 64)
        h.uc.mem_write(0x005E3E9C, b'\xE9' + struct.pack('<i', stub - 0x005E3EA1))
        h.uc.ctl_remove_cache(0x005E3E9C, 0x005E3EA1)

        nodes = [h.alloc(8, bytes(8)) for _ in range(3)]
        sentinel = h.alloc(8, bytes(8))
        obj = h.alloc(0x70, b'\xEE' * 0x70)
        h.uc.mem_write(obj + 0x5c, _dword(sentinel))
        h.uc.mem_write(obj + 0x60, _dword(7))

        def setup(n, cnt):
            h.uc.mem_write(log, bytes(0x40))
            h.uc.mem_write(log + 4, _dword(log + 8))
            for i in range(n):
                h.uc.mem_write(nodes[i], _dword(nodes[i + 1] if i + 1 < n else sentinel) + _dword(sentinel))
            h.uc.mem_write(sentinel, _dword(nodes[0] if n else sentinel)
                           + _dword(nodes[n - 1] if n else sentinel))
            h.uc.mem_write(obj + 0x60, _dword(cnt))

        for n, cnt in ((3, 3), (1, 1), (0, 0)):
            setup(n, cnt)
            diffs = h.compare(0x00426C00, regs={UC_X86_REG_ECX: obj}, ret=None)
            if diffs:
                return ['%d nodes: %s' % (n, d) for d in diffs]
            setup(n, cnt)
            res = h.call(0x00426C00, regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['%d nodes: replacement faulted: %s' % (n, res['fault'])]
            if _u32(h, sentinel) != sentinel or _u32(h, sentinel + 4) != sentinel:
                return ['%d nodes: the sentinel links are %08X / %08X'
                        % (n, _u32(h, sentinel), _u32(h, sentinel + 4))]
            if _u32(h, obj + 0x60) != 0:
                return ['%d nodes: the count is %08X' % (n, _u32(h, obj + 0x60))]
            if _u32(h, log) != n:
                return ['%d nodes: free ran %d times' % (n, _u32(h, log))]
            for i in range(n):
                if _u32(h, log + 8 + 4 * i) != nodes[i]:
                    return ['%d nodes: free %d got %08X' % (n, i, _u32(h, log + 8 + 4 * i))]
        return None
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
