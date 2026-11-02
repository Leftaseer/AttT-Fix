"""The virtual tail call must pass this in ECX and reuse the caller's argument slot."""

import struct


def test_virtual_tail_call(h):
    # A valid thiscall target: record the argument, count calls, then ret 4.
    target = h.alloc(32, bytes.fromhex('8b442404 894104 ff4108 c20400'))
    vtable = h.alloc(4, struct.pack('<I', target))
    obj = h.alloc(12, struct.pack('<III', vtable, 0, 0))
    diffs = h.compare(0x004CC8D0, args=[0], ret=None)
    diffs += h.compare(0x004CC8D0, args=[obj], ret=None)
    result = h.call(0x004CC8D0, args=[obj])
    if result['fault'] or result['esp'] != 8:
        diffs.append('tail call did not return with ret 4: %r' % result)
    if bytes(h.uc.mem_read(obj + 4, 8)) != struct.pack('<II', 1, 1):
        diffs.append('virtual method did not receive this and argument 1 exactly once')
    return diffs
