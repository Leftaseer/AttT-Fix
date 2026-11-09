"""CReadRenderInfo: the light record (0x4A8D70 / 0x4A90D0), the vector<RenderLight> operations (0x4A8C00 ...
0x4A95C0), the singleton's lifetime (0x4A9480 / 0x4A94C0 / 0x4A9570), the loader (0x4A9650) and the accessor
(0x44AE70).

The record is a POD (0x6C bytes: the enabled flag and a D3DLIGHT9), so the vector tests only compare memory.  The
Read and Load tests patch the nScript/Lua callees with small stubs: a field table is a fake 0xC-byte wrapper, a
number is index * 2, the type is 3 and the element count is 2, so both runs see the same script values."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EBX
from difftest import STACK, STACK_SIZE

READ = 0x004A8D70
CTOR_LIGHT = 0x004A90D0
COUNT = 0x004A8C00
FILL = 0x004A8CF0
COPY = 0x004A8D40
COPY_BACKWARD = 0x004A9040
FILL_END = 0x004A9140
COPY_END = 0x004A91B0
INSERT_N = 0x004A91E0
INSERT_ONE = 0x004A9500
PUSH = 0x004A95C0
CTOR_INFO = 0x004A9480
DTOR_INFO = 0x004A94C0
DELETE_INFO = 0x004A9570
LOAD = 0x004A9650
GET_INFO = 0x0044AE70

DO_FILE = 0x00432620
TABLE_FROM_INDEX = 0x0045C7E0
TABLE_FROM_STACK = 0x0045C850
TABLE_DTOR = 0x004220A0
TABLE_ASSIGN = 0x0057A860
GET_BOOL = 0x0057AA20
GET_FLOAT = 0x0057AD40
GET_NUMBER = 0x0057AC90
GET_TABLE = 0x0057B4E0
NORMALIZE = 0x005B8074
OBJECT_DTOR = 0x00422000
LUA_OBJLEN = 0x00402F40
LUA_RAWGETI = 0x00403390
LUA_SETTOP = 0x00402A70

READ_INFO_GLOBAL = 0x006C8C34
TABLE_VTABLE = 0x00607CC4

LIGHT_SIZE = 0x6C
INFO_SIZE = 0x24
NUMBER_STEP = 2.0


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _patch(h, addr, code, saved):
    saved.append((addr, bytes(h.uc.mem_read(addr, len(code)))))
    h.uc.mem_write(addr, code)
    h.uc.ctl_remove_cache(addr, addr + len(code))


def _restore(h, saved):
    for addr, code in reversed(saved):
        h.uc.mem_write(addr, code)
        h.uc.ctl_remove_cache(addr, addr + len(code))


def _stub_table_ctor(h, saved):
    _patch(h, TABLE_FROM_INDEX,
           b'\xc7\x01' + struct.pack('<I', TABLE_VTABLE)   # [ecx] = vftable
           + b'\xc7\x41\x04' + bytes(4)                    # [ecx+4] = 0
           + b'\xc7\x41\x08' + struct.pack('<i', -1)       # [ecx+8] = -1
           + b'\xc2\x04\x00', saved)


def _stub_from_stack(h, saved):
    _patch(h, TABLE_FROM_STACK,
           b'\x8b\x44\x24\x04'                             # eax = out
           + b'\xc7\x00' + struct.pack('<I', TABLE_VTABLE)
           + b'\xc7\x40\x04' + bytes(4)
           + b'\xc7\x40\x08' + struct.pack('<i', 7)
           + b'\xc2\x04\x00', saved)


def _stub_get_table(h, saved):
    _patch(h, GET_TABLE,
           b'\x8b\x44\x24\x04'                             # eax = out
           + b'\xc7\x00' + struct.pack('<I', TABLE_VTABLE)
           + b'\xc7\x40\x04' + bytes(4)
           + b'\xc7\x40\x08' + struct.pack('<i', 5)
           + b'\xc2\x08\x00', saved)


def _stub_assign(h, saved):
    _patch(h, TABLE_ASSIGN,
           b'\x8b\x44\x24\x04'                             # eax = other
           + b'\x8b\x10\x89\x11'                           # [ecx] = [eax]
           + b'\x8b\x50\x04\x89\x51\x04'                   # [ecx+4] = [eax+4]
           + b'\x8b\x50\x08\x89\x51\x08'                   # [ecx+8] = [eax+8]
           + b'\xc2\x04\x00', saved)


def _stub_get_number(h, saved):
    step = h.alloc(4, struct.pack('<f', NUMBER_STEP))
    _patch(h, GET_NUMBER,
           b'\xdb\x44\x24\x04'                             # fild dword [esp+4] (the index)
           + b'\xd8\x0d' + struct.pack('<I', step)         # fmul NUMBER_STEP
           + b'\xc2\x04\x00', saved)


def _stub_get_float(h, saved, value):
    const = h.alloc(4, struct.pack('<f', value))
    _patch(h, GET_FLOAT, b'\xd9\x05' + struct.pack('<I', const) + b'\xc2\x04\x00', saved)


def _stub_get_bool(h, saved, value):
    _patch(h, GET_BOOL, b'\xb0' + bytes([value]) + b'\xc2\x04\x00', saved)


def _stub_table_dtor(h, saved):
    _patch(h, TABLE_DTOR, b'\xc3', saved)


def _stub_normalize(h, saved):
    _patch(h, NORMALIZE, b'\xc2\x08\x00', saved)


def _stub_load_calls(h, saved, count=2):
    # the loader calls the compiled CLuaWrapper::DoFile (the hand translation), not the address 0x432620
    do_file = h.symbols.get('?DoFile@CLuaWrapper@@QAEXPBD@Z', DO_FILE)
    _patch(h, do_file, b'\xc2\x04\x00', saved)                 # DoFile(this, name): ret 4
    _stub_table_ctor(h, saved)
    _stub_from_stack(h, saved)
    _stub_get_table(h, saved)
    _stub_get_number(h, saved)
    _stub_get_bool(h, saved, 1)
    _stub_get_float(h, saved, 3.0)
    _stub_assign(h, saved)
    _stub_normalize(h, saved)
    _stub_table_dtor(h, saved)
    _patch(h, LUA_OBJLEN, b'\xb8' + struct.pack('<I', count) + b'\xc3', saved)
    _patch(h, LUA_RAWGETI, b'\xc3', saved)
    _patch(h, LUA_SETTOP, b'\xc3', saved)
    _patch(h, OBJECT_DTOR, b'\xc3', saved)


def _run(h, addr, args, regs, setup, ret):
    diffs = h.compare(addr, args=args, regs=regs, setup=setup, ret=ret)
    return diffs


def test_render_light_defaults(h):
    """Read with full=false takes the default Enable/Type, then still fills a directional light from the entry:
    the sub-tables are read from the value table, so the stubs apply to this path as well."""
    record = h.alloc(LIGHT_SIZE, bytes([0xA5]) * LIGHT_SIZE)
    saved = []

    def setup(h):
        _stub_get_table(h, saved)
        _stub_assign(h, saved)
        _stub_get_number(h, saved)
        _stub_normalize(h, saved)
        _stub_table_dtor(h, saved)
        h.uc.mem_write(record, bytes([0xA5]) * LIGHT_SIZE)

    try:
        diffs = h.compare(READ, args=[0x12340000, 0], regs={UC_X86_REG_ECX: record}, setup=setup, ret=None)
        if diffs:
            return diffs
        res = h.call(READ, args=[0x12340000, 0], regs={UC_X86_REG_ECX: record})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
    finally:
        _restore(h, saved)
    if h.uc.mem_read(record, 1) != b'\x01':
        return ['the record is not enabled']
    if _u32(h, record + 4) != 3:
        return ['Type is %d, not D3DLIGHT_DIRECTIONAL' % _u32(h, record + 4)]
    numbers = [NUMBER_STEP * i for i in (1, 2, 3, 4)]
    direction = struct.unpack('<3f', h.uc.mem_read(record + 0x44, 12))
    if direction != (numbers[0], numbers[1], numbers[2]):
        return ['Direction is %r' % (direction,)]
    diffuse = struct.unpack('<4f', h.uc.mem_read(record + 0x08, 16))
    if diffuse != tuple(numbers):
        return ['Diffuse is %r' % (diffuse,)]
    return []


def test_render_light_full(h):
    """Read with full=true takes Enable/Type and the four sub-tables; the stubs give every number index * 2."""
    record = h.alloc(LIGHT_SIZE, bytes(LIGHT_SIZE))
    saved = []

    def setup(h):
        _stub_get_bool(h, saved, 1)
        _stub_get_float(h, saved, 3.0)
        _stub_get_table(h, saved)
        _stub_assign(h, saved)
        _stub_get_number(h, saved)
        _stub_table_dtor(h, saved)
        _stub_normalize(h, saved)
        h.uc.mem_write(record, bytes([0x5A]) * LIGHT_SIZE)

    try:
        diffs = h.compare(READ, args=[0x12340000, 1], regs={UC_X86_REG_ECX: record}, setup=setup, ret=None)
        if diffs:
            return diffs
        res = h.call(READ, args=[0x12340000, 1], regs={UC_X86_REG_ECX: record})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
    finally:
        _restore(h, saved)
    numbers = [NUMBER_STEP * i for i in (1, 2, 3, 4)]
    direction = struct.unpack('<3f', h.uc.mem_read(record + 0x44, 12))
    if direction != (numbers[0], numbers[1], numbers[2]):
        return ['Direction is %r' % (direction,)]
    diffuse = struct.unpack('<4f', h.uc.mem_read(record + 0x08, 16))
    if diffuse != tuple(numbers):
        return ['Diffuse is %r' % (diffuse,)]
    ambient = struct.unpack('<4f', h.uc.mem_read(record + 0x28, 16))
    if ambient != tuple(numbers):
        return ['Ambient is %r' % (ambient,)]
    specular = struct.unpack('<4f', h.uc.mem_read(record + 0x18, 16))
    if specular != tuple(numbers):
        return ['Specular is %r' % (specular,)]
    return []


def test_render_light_ctor(h):
    """0x4A90D0 runs Read and returns this; the value table is still read for a directional light."""
    record = h.alloc(LIGHT_SIZE, bytes(LIGHT_SIZE))
    saved = []

    def setup(h):
        _stub_get_table(h, saved)
        _stub_assign(h, saved)
        _stub_get_number(h, saved)
        _stub_normalize(h, saved)
        _stub_table_dtor(h, saved)
        h.uc.mem_write(record, bytes([0xA5]) * LIGHT_SIZE)

    try:
        diffs = h.compare(CTOR_LIGHT, args=[0x12340000, 0], regs={UC_X86_REG_ECX: record}, setup=setup, ret='eax')
        if diffs:
            return diffs
        res = h.call(CTOR_LIGHT, args=[0x12340000, 0], regs={UC_X86_REG_ECX: record})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
    finally:
        _restore(h, saved)
    if res['eax'] != record:
        return ['returned %#x, not this %#x' % (res['eax'], record)]
    return []


def test_render_light_count(h):
    """0x4A8C00 counts the elements and tolerates the null begin."""
    for begin, end in ((0, 0), (0x20000000, 0x20000000), (0x20000000, 0x20000000 + 3 * LIGHT_SIZE)):
        vector = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(vector + 4, struct.pack('<II', begin, end))
        diffs = h.compare(COUNT, regs={UC_X86_REG_ECX: vector}, setup=None, ret='eax')
        if diffs:
            return diffs
    return []


def _make_buffer(h, capacity):
    """a vector buffer of the given capacity; every slot carries its index as a byte pattern"""
    buffer = h.alloc(max(1, capacity) * LIGHT_SIZE, bytes(max(1, capacity) * LIGHT_SIZE))
    for i in range(capacity):
        h.uc.mem_write(buffer + i * LIGHT_SIZE, bytes([i + 1]) * LIGHT_SIZE)
    return buffer


def _put_vector(h, vector, buffer, count, capacity):
    """begin/end/limit of a vector over the buffer (empty when count and capacity are zero)"""
    if count == 0 and capacity == 0:
        h.uc.mem_write(vector, struct.pack('<IIII', 0, 0, 0, 0))
        return 0
    h.uc.mem_write(vector, struct.pack('<IIII', 0, buffer, buffer + count * LIGHT_SIZE,
                                       buffer + capacity * LIGHT_SIZE))
    return buffer


def test_render_light_push_back(h):
    """0x4A95C0 copies into the free slot when there is room and grows the vector otherwise."""
    value = h.alloc(LIGHT_SIZE, bytes([0xEE]) * LIGHT_SIZE)

    for count, capacity in ((0, 0), (1, 2), (2, 2)):
        vector = h.alloc(0x10, bytes(0x10))
        buffer = _make_buffer(h, capacity)

        def setup(h, vector=vector, buffer=buffer, count=count, capacity=capacity):
            _put_vector(h, vector, buffer, count, capacity)

        diffs = h.compare(PUSH, args=[value], regs={UC_X86_REG_ECX: vector}, setup=setup, ret=None)
        if diffs:
            return diffs
        res = h.call(PUSH, args=[value], regs={UC_X86_REG_ECX: vector})
        if res['fault']:
            return ['replacement faulted for %d/%d: %s' % (count, capacity, res['fault'])]
        _, begin, end, limit = struct.unpack('<4I', h.uc.mem_read(vector, 16))
        if begin == 0 or end != begin + (count + 1) * LIGHT_SIZE or limit < end:
            return ['the vector %d/%d ended as %r' % (count, capacity, (begin, end, limit))]
        if bytes(h.uc.mem_read(end - LIGHT_SIZE, LIGHT_SIZE)) != bytes([0xEE]) * LIGHT_SIZE:
            return ['the new element of %d/%d is not the value' % (count, capacity)]
    return []


def test_render_light_insert_one(h):
    """0x4A9500 inserts one element at the caller's position and reports its address in *result."""
    value = h.alloc(LIGHT_SIZE, bytes([0xEE]) * LIGHT_SIZE)

    for count, capacity, at in ((0, 0, 0), (2, 4, 1), (2, 2, 2)):
        vector = h.alloc(0x10, bytes(0x10))
        result = h.alloc(4, bytes(4))
        buffer = _make_buffer(h, capacity)
        position = buffer + at * LIGHT_SIZE if count else 0

        def setup(h, vector=vector, buffer=buffer, count=count, capacity=capacity):
            _put_vector(h, vector, buffer, count, capacity)

        diffs = h.compare(INSERT_ONE, args=[result, position, value], regs={UC_X86_REG_ECX: vector},
                          setup=setup, ret=None)
        if diffs:
            return diffs
        res = h.call(INSERT_ONE, args=[result, position, value], regs={UC_X86_REG_ECX: vector})
        if res['fault']:
            return ['replacement faulted for %d/%d: %s' % (count, capacity, res['fault'])]
        _, begin, end, limit = struct.unpack('<4I', h.uc.mem_read(vector, 16))
        if end != begin + (count + 1) * LIGHT_SIZE or limit < end:
            return ['the vector %d/%d ended as %r' % (count, capacity, (begin, end, limit))]
        element = _u32(h, result)
        if not (begin <= element < end):
            return ['result %#x is outside [%#x, %#x)' % (element, begin, end)]
        if element != begin + at * LIGHT_SIZE:
            return ['result %#x is not element %d' % (element, at)]
        if bytes(h.uc.mem_read(element, LIGHT_SIZE)) != bytes([0xEE]) * LIGHT_SIZE:
            return ['the inserted element is not the value']
    return []


def test_render_light_insert_n(h):
    """0x4A91E0 inserts count elements: grow, shift the tail forward past the free space or move it back."""
    value = h.alloc(LIGHT_SIZE, bytes([0xEE]) * LIGHT_SIZE)
    cases = ((1, 1, 0, 2), (4, 8, 1, 2), (4, 8, 3, 3), (2, 4, 1, 3), (1, 1, 1, 0))

    for count, capacity, at, add in cases:
        vector = h.alloc(0x10, bytes(0x10))
        buffer = _make_buffer(h, capacity)
        position = buffer + at * LIGHT_SIZE

        def setup(h, vector=vector, buffer=buffer, count=count, capacity=capacity):
            _put_vector(h, vector, buffer, count, capacity)

        diffs = h.compare(INSERT_N, args=[position, add, value], regs={UC_X86_REG_ECX: vector},
                          setup=setup, ret=None)
        if diffs:
            return diffs
        res = h.call(INSERT_N, args=[position, add, value], regs={UC_X86_REG_ECX: vector})
        if res['fault']:
            return ['replacement faulted for %d/%d: %s' % (count, capacity, res['fault'])]
        _, begin, end, limit = struct.unpack('<4I', h.uc.mem_read(vector, 16))
        if end != begin + (count + add) * LIGHT_SIZE or limit < end:
            return ['the vector %d/%d ended as %r' % (count, capacity, (begin, end, limit))]
        for i in range(add):
            element = begin + (at + i) * LIGHT_SIZE
            if bytes(h.uc.mem_read(element, LIGHT_SIZE)) != bytes([0xEE]) * LIGHT_SIZE:
                return ['element %d of %d/%d is not the value' % (at + i, count, capacity)]
    return []


def test_render_info_ctor(h):
    """0x4A9480 sets the vtable and empties the vector; the allocator stays as it was."""
    info = h.alloc(INFO_SIZE, bytes(INFO_SIZE))

    def setup(h):
        h.uc.mem_write(info, bytes([0x5A]) * INFO_SIZE)

    diffs = h.compare(CTOR_INFO, regs={UC_X86_REG_ECX: info}, setup=setup, ret='eax')
    if diffs:
        return diffs
    res = h.call(CTOR_INFO, regs={UC_X86_REG_ECX: info})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != info:
        return ['returned %#x, not this %#x' % (res['eax'], info)]
    if struct.unpack('<III', h.uc.mem_read(info + 0x18, 12)) != (0, 0, 0):
        return ['the vector is not empty']
    return []


def test_render_info_dtor(h):
    """0x4A94C0 frees the vector's buffer and drops to the CSingleton vtable."""
    info = h.alloc(INFO_SIZE, bytes(INFO_SIZE))

    def setup(h):
        buffer = h.alloc(3 * LIGHT_SIZE, bytes(3 * LIGHT_SIZE))
        h.uc.mem_write(info, struct.pack('<II', 0xDEADBEEF, 0))
        h.uc.mem_write(info + 0x14, struct.pack('<IIII', 0, buffer, buffer + 3 * LIGHT_SIZE,
                                                buffer + 3 * LIGHT_SIZE))

    diffs = h.compare(DTOR_INFO, regs={UC_X86_REG_ECX: info}, setup=setup, ret=None)
    if diffs:
        return diffs
    res = h.call(DTOR_INFO, regs={UC_X86_REG_ECX: info})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    return []


def test_delete_render_info(h):
    """0x4A9570 destroys the singleton and deletes it only when flag 1 is set; it returns this."""
    diffs = []
    for flags in (0, 1):
        info = h.alloc(INFO_SIZE, bytes(INFO_SIZE))

        def setup(h):
            buffer = h.alloc(3 * LIGHT_SIZE, bytes(3 * LIGHT_SIZE))
            h.uc.mem_write(info, struct.pack('<II', 0xDEADBEEF, 0))
            h.uc.mem_write(info + 0x14, struct.pack('<IIII', 0, buffer, buffer + 3 * LIGHT_SIZE,
                                                    buffer + 3 * LIGHT_SIZE))

        diffs += h.compare(DELETE_INFO, args=[flags], regs={UC_X86_REG_ECX: info}, setup=setup, ret='eax')
        if diffs:
            return diffs
        res = h.call(DELETE_INFO, args=[flags], regs={UC_X86_REG_ECX: info})
        if res['fault']:
            return ['replacement faulted for flag %d: %s' % (flags, res['fault'])]
        if res['eax'] != info:
            diffs.append('flag %d returned %#x, not this %#x' % (flags, res['eax'], info))
    return diffs


def test_load_render_info(h):
    """0x4A9650 runs the chunk, reads the ambient colour and walks the "Light" array (two entries in the stub)."""
    info = h.alloc(INFO_SIZE, bytes(INFO_SIZE))
    saved = []

    def setup(h):
        _stub_load_calls(h, saved, 2)
        # the light record has three padding bytes (after Enable) that Read leaves untouched and the push copies
        # to the vector: zero the scratch stack so both runs read the same value there
        h.uc.mem_write(STACK, bytes(STACK_SIZE))
        h.uc.mem_write(info, bytes(INFO_SIZE))

    try:
        diffs = h.compare(LOAD, regs={UC_X86_REG_ECX: info, UC_X86_REG_EBX: 0}, setup=setup, ret=None)
        if diffs:
            return diffs
        res = h.call(LOAD, regs={UC_X86_REG_ECX: info, UC_X86_REG_EBX: 0})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
    finally:
        _restore(h, saved)
    ambient = struct.unpack('<4f', h.uc.mem_read(info + 4, 16))
    expected = tuple(NUMBER_STEP * i for i in (1, 2, 3, 4))
    if ambient != expected:
        return ['GlobalAmbient is %r' % (ambient,)]
    _, begin, end, limit = struct.unpack('<4I', h.uc.mem_read(info + 0x14, 16))
    if begin == 0 or end != begin + 2 * LIGHT_SIZE or limit < end:
        return ['the light vector is %r' % ((begin, end, limit),)]
    return []


def test_get_read_render_info(h):
    """0x44AE70 builds the singleton once and returns the cached one afterwards."""
    saved = []

    def setup(h):
        h.uc.mem_write(READ_INFO_GLOBAL, bytes(4))

    diffs = h.compare(GET_INFO, setup=setup, ret='eax')
    if diffs:
        return diffs
    res = h.call(GET_INFO)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    instance = _u32(h, READ_INFO_GLOBAL)
    if res['eax'] != instance or instance == 0:
        return ['returned %#x, the global is %#x' % (res['eax'], instance)]
    return []
