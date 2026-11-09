"""CUpdateObject::Update (0x00424D90): the time accumulates, every full interval runs one Tick (slot 5) and the
number of the steps of this frame goes to slot 9.  The vtables are stubbed in the heap."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

UPDATE = 0x00424D90


def _bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def _stubs(h):
    ticks = h.alloc(4, bytes(4))
    calls = h.alloc(4, bytes(4))
    last = h.alloc(4, bytes(4))
    tick_code = (b'\xA1' + struct.pack('<I', ticks) +      # mov eax, [ticks]
                 b'\x40'                                   # inc eax
                 b'\xA3' + struct.pack('<I', ticks) +      # mov [ticks], eax
                 b'\xC3')                                  # ret
    done_code = (b'\x8B\x44\x24\x04'                       # mov eax, [esp+4]  (the step count)
                 b'\xA3' + struct.pack('<I', last) +       # mov [last], eax
                 b'\xA1' + struct.pack('<I', calls) +      # mov eax, [calls]
                 b'\x40'                                   # inc eax
                 b'\xA3' + struct.pack('<I', calls) +      # mov [calls], eax
                 b'\xC2\x04\x00')                          # ret 4
    table = h.alloc(40, bytes(40))
    h.uc.mem_write(table + 20, struct.pack('<I', h.alloc(len(tick_code), tick_code)))
    h.uc.mem_write(table + 36, struct.pack('<I', h.alloc(len(done_code), done_code)))
    return table, ticks, calls, last


def _prepare(h, obj, table, interval, accumulator, ticks, calls, last):
    h.uc.mem_write(obj, struct.pack('<I', table) + bytes(4))
    h.uc.mem_write(obj + 0x24, struct.pack('<ff', interval, accumulator))
    h.uc.mem_write(obj + 0x2C, bytes(12))
    h.uc.mem_write(ticks, bytes(4))
    h.uc.mem_write(calls, bytes(4))
    h.uc.mem_write(last, bytes(4))


def test_update_object(h):
    obj = h.alloc(0x38, bytes(0x38))
    table, ticks, calls, last = _stubs(h)
    cases = [
        (0.25, 0.0, 0.125, 0, 0.125),    # below the interval: nothing yet
        (0.25, 0.0, 0.375, 1, 0.125),    # one step
        (0.25, 0.0, 0.5, 2, 0.0),        # two steps, exactly on the interval
        (0.25, 0.25, 0.0, 1, 0.0),       # already on the interval: one step, no time left
        (0.125, 0.0, 1.0, 8, 0.0),       # a long frame catches up
        (0.25, 0.375, 0.0, 1, 0.125),    # the accumulated time alone is enough
    ]
    for interval, accumulator, dt, want_ticks, want_acc in cases:
        _prepare(h, obj, table, interval, accumulator, ticks, calls, last)
        diffs = h.compare(UPDATE, args=[_bits(dt)], regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return ['interval %r acc %r dt %r: %s' % (interval, accumulator, dt, d) for d in diffs]
        _prepare(h, obj, table, interval, accumulator, ticks, calls, last)
        res = h.call(UPDATE, args=[_bits(dt)], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['interval %r acc %r dt %r: replacement faulted: %s'
                    % (interval, accumulator, dt, res['fault'])]
        got_ticks = struct.unpack('<I', h.uc.mem_read(ticks, 4))[0]
        got_calls = struct.unpack('<I', h.uc.mem_read(calls, 4))[0]
        got_last = struct.unpack('<I', h.uc.mem_read(last, 4))[0]
        got_acc = struct.unpack('<f', h.uc.mem_read(obj + 0x28, 4))[0]
        if got_ticks != want_ticks:
            return ['interval %r acc %r dt %r: %d ticks, want %d'
                    % (interval, accumulator, dt, got_ticks, want_ticks)]
        if want_ticks:
            if got_calls != 1 or got_last != want_ticks:
                return ['interval %r acc %r dt %r: slot 9 called %d times with %d, want once with %d'
                        % (interval, accumulator, dt, got_calls, got_last, want_ticks)]
        elif got_calls:
            return ['interval %r acc %r dt %r: slot 9 called without a step'
                    % (interval, accumulator, dt)]
        if got_acc != want_acc:
            return ['interval %r acc %r dt %r: accumulator %r, want %r'
                    % (interval, accumulator, dt, got_acc, want_acc)]
    return None
