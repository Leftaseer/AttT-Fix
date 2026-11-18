"""0x4313A0 span-array serialization; ostream::write is a recording stub."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x004313A0
IAT_WRITE = 0x006071B0
WRITE_SYMBOL = '__imp_?write@?$basic_ostream@DU?$char_traits@D@std@@@std@@QAEAAV12@PBDH@Z'
LOG_COUNT = 0x00
LOG_THIS = 0x04
LOG_BUFS = 0x10
LOG_SIZES = 0x60
LOG_SIZE = 0xB0
saved = {}


def _dword(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _u32(h, address):
    return struct.unpack('<I', h.uc.mem_read(address, 4))[0]


def _patch(h, address, data):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(data))))
    h.uc.mem_write(address, data)
    h.uc.ctl_remove_cache(address, address + len(data))


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _case(h, log, stream, count):
    records = h.alloc(max(1, count * 0xc), bytes(max(1, count * 0xc)))
    payloads = []
    obj = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(obj + 4, _dword(0xAAAAAAAA))
    h.uc.mem_write(obj + 8, _dword(count))
    for index in range(count):
        payload = h.alloc(4, bytes((0x40 + index, 0x50 + index, 0x60 + index, 0x70 + index)))
        payloads.append(payload)
        record = records + index * 0xc
        h.uc.mem_write(record, _dword(payload))
        h.uc.mem_write(record + 4, _dword(4))
        h.uc.mem_write(record + 8, _dword(0xD0000000 + index))
    h.uc.mem_write(obj, _dword(records))

    diffs = h.compare(FN, args=(stream,), regs={UC_X86_REG_ECX: obj}, ret='eax')
    if diffs:
        return ['count %d: %s' % (count, d) for d in diffs]
    h.uc.mem_write(log, bytes(LOG_SIZE))
    result = h.call(FN, args=(stream,), regs={UC_X86_REG_ECX: obj})
    if result['fault']:
        return ['count %d: %s' % (count, result['fault'])]

    expected = [(obj + 4, 4), (obj + 8, 4)]
    for index in range(count):
        record = records + index * 0xc
        expected += [(record + 4, 4), (record + 8, 4), (payloads[index], 4)]
    problems = []
    if _u32(h, log + LOG_COUNT) != len(expected):
        problems.append('count %d: wrote %d times, want %d' % (count, _u32(h, log + LOG_COUNT), len(expected)))
    if _u32(h, log + LOG_THIS) != stream:
        problems.append('count %d: stream is %#x' % (count, _u32(h, log + LOG_THIS)))
    for index, (buffer, size) in enumerate(expected):
        got_buffer = _u32(h, log + LOG_BUFS + index * 4)
        got_size = _u32(h, log + LOG_SIZES + index * 4)
        if (got_buffer, got_size) != (buffer, size):
            problems.append('count %d: write %d is (%#x, %#x), want (%#x, %#x)' %
                            (count, index, got_buffer, got_size, buffer, size))
    base = stream if not count else obj + 8
    want_result = (base & 0xFFFFFF00) | 1
    if result['eax'] != want_result:
        problems.append('count %d: result is %#x, want %#x' % (count, result['eax'], want_result))
    return problems


def test_span_array_serialize(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        stream = h.alloc(0x40, bytes(0x40))
        code = (b'\x89\x0D' + _dword(log + LOG_THIS)
                + b'\x8B\x05' + _dword(log + LOG_COUNT)
                + b'\x8B\x54\x24\x04'
                + b'\x89\x14\x85' + _dword(log + LOG_BUFS)
                + b'\x8B\x54\x24\x08'
                + b'\x89\x14\x85' + _dword(log + LOG_SIZES)
                + b'\xFF\x05' + _dword(log + LOG_COUNT)
                + b'\x8B\xC1'
                + b'\xC2\x08\x00')
        stub = h.alloc(len(code), code)
        h.uc.ctl_remove_cache(stub, stub + len(code))
        for slot in (IAT_WRITE, h.symbols[WRITE_SYMBOL]):
            _patch(h, slot, _dword(stub))

        problems = []
        for count in (0, 1, 3):
            problems += _case(h, log, stream, count)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
