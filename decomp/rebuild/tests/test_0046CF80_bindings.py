"""CInput's key bindings in inputbind.cpp: 0x46CF80 blanks every binding, 0x46ED10 replaces a binding's sequence
with one key code found by the lowercase command name, 0x46EDC0 does the same with the code of a DIK name, and
0x46F480 gives the command id of a name (0 when the name is not in the command map).

The command map (+0x690) is the string-keyed FsHashMap of the map tests: the bucket vector at +14 holds one node
pointer per bucket plus the list end, the nodes are {next; prev; std::string key; command id}.  A binding
(+0x6BC) is {vtable; sequence; length}; the sequence of a fresh binding holds the terminator byte at [0]."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

CLEAR = 0x0046CF80
SET = 0x0046ED10
SET_BY_NAME = 0x0046EDC0
BINDING_COMMAND = 0x0046F480

UNTOUCHED = 0xEE
MASK = 1
BUCKETS = 1

COMMANDS = [(b'move', 0), (b'attack', 1), (b'use', 2)]


def _put_string(h, addr, text=b''):
    """a VC8 string: allocator, inline buffer, size, capacity"""
    assert len(text) < 16
    h.uc.mem_write(addr, bytes(4))
    h.uc.mem_write(addr + 4, text + b'\0' * (16 - len(text)))
    h.uc.mem_write(addr + 20, struct.pack('<II', len(text), 15))


def _string(h, text):
    s = h.alloc(28, bytes(28))
    _put_string(h, s, text)
    return s


def _make_command_map(h, entries):
    """the case-sensitive string map of entries (key bytes, command id), every key in bucket 0, keys ascending"""
    entries = sorted(entries, key=lambda e: e[0])
    mapobj = h.alloc(0x28, bytes(0x28))
    sentinel = h.alloc(0x10, bytes(0x10))
    nodes = []
    for key, value in entries:
        node = h.alloc(0x28, bytes(0x28))
        _put_string(h, node + 8, key)
        h.uc.mem_write(node + 0x24, struct.pack('<I', value))
        nodes.append(node)
    ring = [sentinel] + nodes + [sentinel]
    for here, following in zip(ring, ring[1:]):
        h.uc.mem_write(here, struct.pack('<I', following))
    for here, previous in zip(ring[1:], ring):
        h.uc.mem_write(here + 4, struct.pack('<I', previous))

    buckets = h.alloc((BUCKETS + 1) * 4, bytes((BUCKETS + 1) * 4))
    for i in range(BUCKETS + 1):
        first = nodes[0] if i == 0 else sentinel
        h.uc.mem_write(buckets + 4 * i, struct.pack('<I', first))

    h.uc.mem_write(mapobj, struct.pack('<IIIIIIIII', 0, 0, sentinel, len(entries), 0,
                                       buckets, buckets + 4 * (BUCKETS + 1), buckets + 4 * (BUCKETS + 1), MASK))
    h.uc.mem_write(mapobj + 0x24, struct.pack('<I', BUCKETS))
    return mapobj


def _make_input(h, entries):
    """a CInput whose command map holds entries and whose bindings start as one terminator byte each"""
    mapobj = _make_command_map(h, entries)
    inp = h.alloc(0x7CC, bytes(0x7CC))
    h.uc.mem_write(inp + 0x68C, struct.pack('<i', len(entries)))
    h.uc.mem_write(inp + 0x690, bytes(h.uc.mem_read(mapobj, 0x28)))
    array = h.alloc(len(entries) * 0x0C, bytes(len(entries) * 0x0C))
    sequences = []
    for i in range(len(entries)):
        sequence = h.alloc(16, bytes([UNTOUCHED]) * 16)
        h.uc.mem_write(array + i * 0x0C, struct.pack('<III', 0, sequence, 1))
        sequences.append(sequence)
    h.uc.mem_write(inp + 0x6BC, struct.pack('<I', array))
    h.uc.mem_write(inp + 0x6C0, struct.pack('<I', len(entries)))
    return inp, array, sequences


def _binding(h, array, sequences, i):
    _vftable, sequence, length = struct.unpack('<III', h.uc.mem_read(array + i * 0x0C, 0x0C))
    assert sequence == sequences[i], 'binding %d lost its sequence' % i
    first = h.uc.mem_read(sequence, 1)[0]
    return length, first


def test_clear_bindings(h):
    inp, array, sequences = _make_input(h, COMMANDS)
    diffs = h.compare(CLEAR, regs={UC_X86_REG_ECX: inp}, ret=None)
    if diffs:
        return diffs
    res = h.call(CLEAR, regs={UC_X86_REG_ECX: inp})
    if res['fault']:
        return ['replacement faulted: %s' % (res['fault'],)]
    for i in range(len(COMMANDS)):
        length, first = _binding(h, array, sequences, i)
        if (length, first) != (1, 0):
            return ['binding %d after clear: length %d, first %#x (want 1, 0)' % (i, length, first)]
    return None


def test_set_binding(h):
    cases = [('ATTACK', 1, 0x41), ('move', 0, 0x10), ('Use', 2, 0x99)]
    for name, index, code in cases:
        inp, array, sequences = _make_input(h, COMMANDS)
        args = [_string(h, name.encode('latin1')), code]
        diffs = h.compare(SET, args=args, regs={UC_X86_REG_ECX: inp}, ret=None)
        if diffs:
            return ['%r: %s' % (name, d) for d in diffs]
        res = h.call(SET, args=args, regs={UC_X86_REG_ECX: inp})
        if res['fault']:
            return ['%r: replacement faulted: %s' % (name, res['fault'])]
        for i in range(len(COMMANDS)):
            length, first = _binding(h, array, sequences, i)
            want = (1, code) if i == index else (1, UNTOUCHED)
            if (length, first) != want:
                return ['%r: binding %d is (%d, %#x), want (%d, %#x)' % (name, i, length, first, want[0], want[1])]
    return None


def test_set_binding_by_name(h):
    cases = [('move', b'SPACE', 0, 57), ('attack', b'A', 1, 30), ('use', b'up', 2, 200),
             ('move', b'xyz', 0, 0xFF)]
    for name, keyname, index, code in cases:
        inp, array, sequences = _make_input(h, COMMANDS)
        args = [_string(h, name.encode('latin1')), _string(h, keyname)]
        diffs = h.compare(SET_BY_NAME, args=args, regs={UC_X86_REG_ECX: inp}, ret=None)
        if diffs:
            return ['%r/%r: %s' % (name, keyname, d) for d in diffs]
        res = h.call(SET_BY_NAME, args=args, regs={UC_X86_REG_ECX: inp})
        if res['fault']:
            return ['%r/%r: replacement faulted: %s' % (name, keyname, res['fault'])]
        for i in range(len(COMMANDS)):
            length, first = _binding(h, array, sequences, i)
            want = (1, code) if i == index else (1, UNTOUCHED)
            if (length, first) != want:
                return ['%r/%r: binding %d is (%d, %#x), want (%d, %#x)'
                        % (name, keyname, i, length, first, want[0], want[1])]
    return None


def test_binding_command(h):
    inp, _array, _sequences = _make_input(h, COMMANDS)
    for name, want in (('attack', 1), ('MOVE', 0), ('Use', 2), ('nope', 0), ('', 0)):
        args = [_string(h, name.encode('latin1'))]
        diffs = h.compare(BINDING_COMMAND, args=args, regs={UC_X86_REG_ECX: inp})
        if diffs:
            return ['%r: %s' % (name, d) for d in diffs]
        res = h.call(BINDING_COMMAND, args=args, regs={UC_X86_REG_ECX: inp})
        if res['fault']:
            return ['%r: replacement faulted: %s' % (name, res['fault'])]
        if res['eax'] != want:
            return ['%r: returned %d, want %d' % (name, res['eax'], want)]
    return None
