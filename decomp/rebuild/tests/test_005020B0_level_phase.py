"""sub_005020B0 (752 bytes, ECX thiscall, ret 0): the tactical level's action phase (+0x64).  A unit is between
actions when its +0x394 state is 0 or 9.  The test stubs the three callees (0x00511B30 the board placement,
0x00501EB0 the army start, 0x004FB660 the target-tree release), drives every phase, and compares against the
original: the placements and their slots, the phase change to 2, the target head relinked empty (count 0), the
defender army's +0xB8 marked only in phase 4, and the failures while a unit is still busy."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x005020B0
PLACE = 0x00511B30
START = 0x00501EB0
CLEAR = 0x004FB660

L_SEQ = 0x00
L_OPS = 0x04
L_PLACE_N = 0x44
L_PLACE = 0x48
L_START_SELF = 0x88
L_START_ARG = 0x8C
L_CLEAR_SELF = 0x90
L_CLEAR_NODE = 0x94
LOG_SIZE = 0xC0

OP_PLACE = 1
OP_START = 2
OP_CLEAR = 3

BUSY = 5                                   # an action state that is neither 0 nor 9

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(v):
    return struct.pack('<I', v)


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _patch_callee(h, address, code):
    """the original body calls the entry; the rebuilt code may also call the compiled body directly"""
    for target in {address, h.symbols.get('_sub_%08X' % address), h.symbols.get('_f_%08X' % address)} - {None}:
        thunk = _stub(h, code)
        _patch(h, target, b'\xE9' + struct.pack('<i', thunk - (target + 5)))


def _restore(h):
    for address, code in saved.items():
        h.uc.mem_write(address, code)
        h.uc.ctl_remove_cache(address, address + len(code))
    saved.clear()


def _stamp(log, op):
    return (b'\xA1' + _dword(log + L_SEQ)                                  # mov eax, [sequence]
            + b'\xFF\x05' + _dword(log + L_SEQ)                            # inc [sequence]
            + b'\xC7\x04\x85' + _dword(log + L_OPS) + _dword(op))          # mov [ops + eax*4], op


def _install(h, log):
    _patch_callee(h, PLACE,
                  _stamp(log, OP_PLACE)
                  + b'\xA1' + _dword(log + L_PLACE_N)                      # mov eax, [placements]
                  + b'\xFF\x05' + _dword(log + L_PLACE_N)                  # inc [placements]
                  + b'\x8D\x04\xC5' + _dword(log + L_PLACE)                # lea eax, [eax*8 + records]
                  + b'\x89\x08'                                            # mov [eax], ecx
                  + b'\x8B\x4C\x24\x04'                                    # mov ecx, [esp+4]
                  + b'\x89\x48\x04'                                        # mov [eax+4], ecx
                  + b'\xC2\x04\x00')                                       # ret 4
    _patch_callee(h, START,
                  _stamp(log, OP_START)
                  + b'\x89\x0D' + _dword(log + L_START_SELF)               # mov [start.self], ecx
                  + b'\x8B\x44\x24\x04'                                    # mov eax, [esp+4]
                  + b'\xA3' + _dword(log + L_START_ARG)                    # mov [start.arg], eax
                  + b'\xC2\x04\x00')                                       # ret 4
    _patch_callee(h, CLEAR,
                  _stamp(log, OP_CLEAR)
                  + b'\x89\x0D' + _dword(log + L_CLEAR_SELF)               # mov [clear.self], ecx
                  + b'\x8B\x44\x24\x04'                                    # mov eax, [esp+4]
                  + b'\xA3' + _dword(log + L_CLEAR_NODE)                   # mov [clear.node], eax
                  + b'\xC2\x04\x00')                                       # ret 4


class Scene:
    def __init__(self, h):
        self.level = h.alloc(0x200, bytes(0x200))
        self.board = h.alloc(0x40, bytes(0x40))
        self.units = [h.alloc(0x398, bytes(0x398)) for _ in range(6)]
        self.placements = h.alloc(0x40, bytes(0x40))
        self.attacker = h.alloc(0xC0, bytes(0xC0))
        self.defender = h.alloc(0xC0, bytes(0xC0))
        self.attacker_units = h.alloc(0x40, bytes(0x40))
        self.defender_units = h.alloc(0x40, bytes(0x40))
        self.head = h.alloc(0x10, bytes(0x10))
        self.node = h.alloc(0x10, bytes(0x10))

    def setup(self, h, phase, board_states=(), attacker_states=(), defender_states=(),
              placements=(), defender_flag=0):
        board = [self.units[i] for i in range(len(board_states))]
        for addr, state in zip(self.units, board_states):
            h.uc.mem_write(addr + 0x394, _dword(state))
        for i, u in enumerate(board):
            h.uc.mem_write(self.board + 4 * i, _dword(u))
        for troop, array, states, first in ((self.attacker, self.attacker_units, attacker_states, 3),
                                            (self.defender, self.defender_units, defender_states, 5)):
            for i, state in enumerate(states):
                u = self.units[first + i]
                h.uc.mem_write(u + 0x394, _dword(state))
                h.uc.mem_write(array + 4 * i, _dword(u))
            h.uc.mem_write(troop + 0x58, _dword(array))
            h.uc.mem_write(troop + 0x5c, _dword(len(states)))
        for i, (u, slot) in enumerate(placements):
            h.uc.mem_write(self.placements + 8 * i, _dword(self.units[u]) + _dword(slot))
        h.uc.mem_write(self.defender + 0xb8, bytes([defender_flag]))
        h.uc.mem_write(self.head, _dword(0xDEAD0001) + _dword(self.node) + _dword(0xDEAD0002))
        fields = ((0x14, self.board), (0x18, len(board)), (0x64, phase), (0xe0, self.placements),
                  (0xe4, len(placements)), (0xe8, self.attacker), (0xec, self.defender),
                  (0x120, self.head), (0x124, 7))
        for off, value in fields:
            h.uc.mem_write(self.level + off, _dword(value))


def _fresh(h, log, scene, **kw):
    def setup(hh):
        hh.uc.mem_write(log, bytes(LOG_SIZE))
        scene.setup(hh, **kw)
    return setup


def _ops(h, log):
    n = _u32(h, log + L_SEQ)
    return [_u32(h, log + L_OPS + 4 * i) for i in range(n)]


def _check(h, scene, log, diffs, phase, want_ops, want_ret, **kw):
    """the original and the replacement agree, then the detailed run of the replacement"""
    compare = _fresh(h, log, scene, phase=phase, **kw)
    d = h.compare(FN, regs={UC_X86_REG_ECX: scene.level}, setup=compare, ret='al')
    if d:
        diffs.extend(d)
        return
    compare(h)
    res = h.call(FN, regs={UC_X86_REG_ECX: scene.level})
    if res['fault']:
        diffs.append('replacement faulted: %s' % res['fault'])
        return
    if (res['eax'] & 0xFF) != want_ret:
        diffs.append('phase %d returned %d, want %d' % (phase, res['eax'] & 0xFF, want_ret))
    if res['esp'] != 4:
        diffs.append('phase %d left esp at %d, want the ret to pop one return address' % (phase, res['esp']))
    ops = _ops(h, log)
    if ops != want_ops:
        diffs.append('phase %d ran %r, want %r' % (phase, ops, want_ops))
    return ops


def test_phase0_places(h):
    heap0 = h.heap_ptr
    diffs = []
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        scene = Scene(h)
        _install(h, log)
        ops = _check(h, scene, log, diffs, 0, [OP_PLACE, OP_PLACE], 1,
                     board_states=(0, 9), placements=((0, 11), (1, 22)))
        if ops is None:
            return diffs
        if _u32(h, scene.level + 0x64) != 0:
            diffs.append('the deploy phase changed the phase')
        got = [(_u32(h, log + L_PLACE + 8 * i), _u32(h, log + L_PLACE + 8 * i + 4)) for i in range(2)]
        if got != [(scene.units[0], 11), (scene.units[1], 22)]:
            diffs.append('the placements logged %r' % (got,))
    finally:
        _restore(h)
        h.heap_ptr = heap0
    return diffs or None


def test_phase0_waits_for_busy_unit(h):
    heap0 = h.heap_ptr
    diffs = []
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        scene = Scene(h)
        _install(h, log)
        _check(h, scene, log, diffs, 0, [], 0,
               board_states=(0, BUSY), placements=((0, 11),))
        if _u32(h, log + L_PLACE_N) != 0:
            diffs.append('a placement ran while the board was busy')
    finally:
        _restore(h)
        h.heap_ptr = heap0
    return diffs or None


def test_phase1_starts_the_army(h):
    heap0 = h.heap_ptr
    diffs = []
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        scene = Scene(h)
        _install(h, log)
        _check(h, scene, log, diffs, 1, [OP_PLACE, OP_PLACE, OP_START], 0,
               attacker_states=(0, 9), placements=((0, 11), (1, 22)))
        if _u32(h, log + L_START_SELF) != scene.level or _u32(h, log + L_START_ARG) != 1:
            diffs.append('the start got (%08X, %d)'
                         % (_u32(h, log + L_START_SELF), _u32(h, log + L_START_ARG)))
        if _u32(h, scene.level + 0x64) != 2:
            diffs.append('the phase is %d, want 2' % _u32(h, scene.level + 0x64))
    finally:
        _restore(h)
        h.heap_ptr = heap0
    return diffs or None


def test_phase1_waits_for_the_attacker(h):
    heap0 = h.heap_ptr
    diffs = []
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        scene = Scene(h)
        _install(h, log)
        _check(h, scene, log, diffs, 1, [], 0,
               attacker_states=(BUSY,), placements=((0, 11),))
        if _u32(h, scene.level + 0x64) != 1:
            diffs.append('the blocked phase changed to %d' % _u32(h, scene.level + 0x64))
    finally:
        _restore(h)
        h.heap_ptr = heap0
    return diffs or None


def test_phase2_clears_the_targets(h):
    heap0 = h.heap_ptr
    diffs = []
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        scene = Scene(h)
        _install(h, log)
        _check(h, scene, log, diffs, 2, [OP_CLEAR], 1,
               attacker_states=(0,), defender_states=(9,))
        if _u32(h, log + L_CLEAR_SELF) != scene.level + 0x11c or _u32(h, log + L_CLEAR_NODE) != scene.node:
            diffs.append('the clear got (%08X, %08X), want (%08X, %08X)'
                         % (_u32(h, log + L_CLEAR_SELF), _u32(h, log + L_CLEAR_NODE),
                            scene.level + 0x11c, scene.node))
        if _u32(h, scene.head) != scene.head or _u32(h, scene.head + 4) != scene.head \
                or _u32(h, scene.head + 8) != scene.head or _u32(h, scene.level + 0x124) != 0:
            diffs.append('the target head was not relinked empty')
        if (h.uc.mem_read(scene.defender + 0xb8, 1))[0] != 0:
            diffs.append('the phase 2 marked the defender army')
    finally:
        _restore(h)
        h.heap_ptr = heap0
    return diffs or None


def test_phase3_only_waits(h):
    heap0 = h.heap_ptr
    diffs = []
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        scene = Scene(h)
        _install(h, log)
        _check(h, scene, log, diffs, 3, [], 1,
               attacker_states=(0,), defender_states=(9,))
        if (h.uc.mem_read(scene.defender + 0xb8, 1))[0] != 0:
            diffs.append('the phase 3 marked the defender army')
        if _u32(h, scene.level + 0x124) != 7:
            diffs.append('the phase 3 dropped the target count')
    finally:
        _restore(h)
        h.heap_ptr = heap0
    return diffs or None


def test_phase3_waits_for_the_defender(h):
    heap0 = h.heap_ptr
    diffs = []
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        scene = Scene(h)
        _install(h, log)
        _check(h, scene, log, diffs, 3, [], 0,
               attacker_states=(0,), defender_states=(BUSY,))
    finally:
        _restore(h)
        h.heap_ptr = heap0
    return diffs or None


def test_phase4_clears_and_marks(h):
    heap0 = h.heap_ptr
    diffs = []
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        scene = Scene(h)
        _install(h, log)
        _check(h, scene, log, diffs, 4, [OP_CLEAR], 1,
               attacker_states=(0,), defender_states=(9,))
        if (h.uc.mem_read(scene.defender + 0xb8, 1))[0] != 1:
            diffs.append('the phase 4 did not mark the defender army')
        if _u32(h, scene.level + 0x124) != 0:
            diffs.append('the phase 4 did not drop the target count')
    finally:
        _restore(h)
        h.heap_ptr = heap0
    return diffs or None


def test_phase4_keeps_an_existing_mark(h):
    heap0 = h.heap_ptr
    diffs = []
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        scene = Scene(h)
        _install(h, log)
        _check(h, scene, log, diffs, 4, [OP_CLEAR], 1,
               attacker_states=(0,), defender_states=(9,), defender_flag=1)
        if (h.uc.mem_read(scene.defender + 0xb8, 1))[0] != 1:
            diffs.append('the existing mark changed')
    finally:
        _restore(h)
        h.heap_ptr = heap0
    return diffs or None


def test_phase4_waits_for_a_busy_unit(h):
    heap0 = h.heap_ptr
    diffs = []
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        scene = Scene(h)
        _install(h, log)
        _check(h, scene, log, diffs, 4, [], 0,
               attacker_states=(BUSY,), defender_states=(9,))
        if (h.uc.mem_read(scene.defender + 0xb8, 1))[0] != 0:
            diffs.append('a blocked phase 4 marked the defender army')
    finally:
        _restore(h)
        h.heap_ptr = heap0
    return diffs or None


def test_unknown_phase_does_nothing(h):
    heap0 = h.heap_ptr
    diffs = []
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        scene = Scene(h)
        _install(h, log)
        _check(h, scene, log, diffs, 5, [], 0,
               attacker_states=(0,), defender_states=(0,))
        if _u32(h, scene.level + 0x124) != 7:
            diffs.append('the unknown phase dropped the target count')
    finally:
        _restore(h)
        h.heap_ptr = heap0
    return diffs or None
