"""0x48AFB0 (index range merge): overlapping or touching 16-bit index ranges are merged, the
selected indices are copied into a buffer locked through vf2C, and the buffer is released through
vf30.  Both vtable entries are stubbed."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

MERGE = 0x0048AFB0

saved = {}


def _dword(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _u32(h, address):
    return struct.unpack('<I', h.uc.mem_read(address, 4))[0]


def _patch(h, address, data):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(data))))
    h.uc.mem_write(address, data)


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _lock_stub(h, log, buffer):
    """vf2C(self, off, size, &data, flags): logs the arguments and hands out buffer"""
    code = (b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log) +                # mov eax,[esp+4]; mov [log],eax
            b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + 4) +            # mov eax,[esp+8]; mov [log+4],eax
            b'\x8B\x44\x24\x0C' + b'\xA3' + _dword(log + 8) +            # mov eax,[esp+0xC]; mov [log+8],eax
            b'\x8B\x44\x24\x14' + b'\xA3' + _dword(log + 0xC) +          # mov eax,[esp+0x14]; mov [log+0xC],eax
            b'\x8B\x44\x24\x10' +                                        # mov eax,[esp+0x10] (&data)
            b'\xB9' + _dword(buffer) +                                    # mov ecx,buffer
            b'\x89\x08' +                                                 # mov [eax],ecx
            b'\x89\x0D' + _dword(log + 0x10) +                            # mov [log+0x10],ecx
            b'\x33\xC0' + b'\xC2\x14\x00')                                # xor eax,eax; ret 0x14
    return _stub(h, code)


def _release_stub(h, log):
    code = (b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log) +                # mov eax,[esp+4]; mov [log],eax
            b'\x33\xC0' + b'\xC2\x04\x00')                                # xor eax,eax; ret 4
    return _stub(h, code)


def _check(h, ranges, expected_merged):
    heap0 = h.heap_ptr
    log = h.alloc(0x40, bytes(0x40))
    rlog = h.alloc(0x10, bytes(0x10))
    buffer = h.alloc(0x80, b'\xCC' * 0x80)
    lock = _lock_stub(h, log, buffer)
    release = _release_stub(h, rlog)
    try:
        vtable = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(vtable + 0x2c, _dword(lock))
        h.uc.mem_write(vtable + 0x30, _dword(release))
        renderer = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(renderer, _dword(vtable))

        source = h.alloc(0x80, bytes(0x80))
        h.uc.mem_write(source, b''.join(struct.pack('<H', 1000 + i) for i in range(0x40)))
        inp = h.alloc(max(8, len(ranges) * 8), b'\x5A' * max(8, len(ranges) * 8))
        for index, (start, end) in enumerate(ranges):
            h.uc.mem_write(inp + index * 8, _dword(start) + _dword(end))
        merged = h.alloc(0x80, b'\xEE' * 0x80)
        obj = h.alloc(0x48, bytes(0x48))
        h.uc.mem_write(obj + 0x38, _dword(inp))
        h.uc.mem_write(obj + 0x3c, struct.pack('<H', len(ranges)))
        h.uc.mem_write(obj + 0x40, _dword(merged))
        h.uc.mem_write(obj + 0x44, b'\xEE\xEE')
        h.uc.mem_write(obj + 0x46, b'\xAA')
        count = h.alloc(4, b'\xFF\xFF\xFF\xFF')

        diffs = h.compare(MERGE, args=[renderer, source, count], regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return ['ranges %r: %s' % (ranges, d) for d in diffs]

        h.uc.mem_write(log, bytes(0x40))
        h.uc.mem_write(rlog, bytes(0x10))
        h.uc.mem_write(buffer, b'\xCC' * 0x80)
        result = h.call(MERGE, args=[renderer, source, count], regs={UC_X86_REG_ECX: obj})
        if result['fault']:
            return ['ranges %r: %s' % (ranges, result['fault'])]

        problems = []
        if bytes(h.uc.mem_read(obj + 0x3c, 2)) != bytes(2):
            problems.append('ranges %r: the count was not cleared' % (ranges,))
        if bytes(h.uc.mem_read(obj + 0x46, 1)) != bytes(1):
            problems.append('ranges %r: +0x46 was not cleared' % (ranges,))
        got = [value for index in range(len(expected_merged))
               for value in (_u32(h, merged + index * 8), _u32(h, merged + index * 8 + 4))]
        expected = [value for pair in expected_merged for value in pair]
        if got != expected:
            problems.append('ranges %r: merged %r' % (ranges, got))
        if (_u32(h, obj + 0x44) & 0xFFFF) != len(expected_merged):
            problems.append('ranges %r: merge count %d' % (ranges, _u32(h, obj + 0x44) & 0xFFFF))
        copied = []
        for start, end in expected_merged:
            copied.extend(range(1000 + start, 1000 + end))
        if _u32(h, count) != len(copied):
            problems.append('ranges %r: copied count %d' % (ranges, _u32(h, count)))
        want = b''.join(struct.pack('<H', value) for value in copied)
        if bytes(h.uc.mem_read(buffer, len(want))) != want:
            problems.append('ranges %r: the buffer holds %r' % (ranges, bytes(h.uc.mem_read(buffer, len(want)))))
        if bytes(h.uc.mem_read(buffer + len(want), 2)) != b'\xCC\xCC':
            problems.append('ranges %r: the buffer was overrun' % (ranges,))
        if (_u32(h, log), _u32(h, log + 4), _u32(h, log + 8), _u32(h, log + 0xC), _u32(h, log + 0x10)) != \
                (renderer, 0, 0, 0, buffer):
            problems.append('ranges %r: the lock got (%#x, %#x, %#x, %#x, %#x)'
                            % (ranges, _u32(h, log), _u32(h, log + 4), _u32(h, log + 8),
                               _u32(h, log + 0xC), _u32(h, log + 0x10)))
        if _u32(h, rlog) != renderer:
            problems.append('ranges %r: the release got %#x' % (ranges, _u32(h, rlog)))
        return problems
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_merge_touching_and_gapped_ranges(h):
    """(2,4)+(4,7) merge, (10,11) stays, the tail (20,25) is appended"""
    return _check(h, [(2, 4), (4, 7), (10, 11), (20, 25)],
                  [(2, 7), (10, 11), (20, 25)])


def test_merge_chain_into_one_run(h):
    """all three ranges overlap or touch, so a single run consumes the tail as well"""
    return _check(h, [(0, 2), (1, 3), (3, 5)], [(0, 5)])


def test_merge_empty_and_single(h):
    problems = _check(h, [], [])
    problems += _check(h, [(4, 9)], [(4, 9)])
    return problems or None
