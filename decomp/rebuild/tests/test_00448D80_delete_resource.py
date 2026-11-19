"""0x00448D80 (ECX = the resource manager, one stack argument -- the name --, ret 4): looks the name up in the hash
map at +4 (0x00422D80 also reports the map's end node at +0xC when the name is unknown).  An unknown name builds
"Попытка удалить не загруженный ресурс с именем " plus the name by 0x00607324 / 0x006071C0 / 0x00607334 and throws
it through 0x005E3EC0 with the throw info at 0x0069916C.  The node's +0x24 object, when present, is released
through vtable slot 0x74 with flag 1 and the node is erased from the map (0x0047CA20).  The lookup, the erase and
the release are stubs that log what they see; the throw thunk is replaced by a returning one so that the continue
path behind it can be compared too (the original relies on the throw never returning)."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x00448D80
FIND = 0x00422D80
ERASE = 0x0047CA20
THROW = 0x005E3EC0

L_NODE = 0x00
L_MAP = 0x04
L_KEY = 0x08
L_ERASE_MAP = 0x0C
L_ERASE_SLOT = 0x10
L_ERASE_NODE = 0x14
L_REL_OBJ = 0x18
L_REL_FLAG = 0x1C
LOG_SIZE = 0x40

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def test_00448D80(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch(h, FIND,
               b'\x8B\x44\x24\x04'                                        # mov eax, [esp+4] (out slot)
               + b'\x8B\x15' + _dword(log + L_NODE)                       # mov edx, [log+NODE]
               + b'\x89\x10'                                              # mov [eax], edx
               + b'\x89\x0D' + _dword(log + L_MAP)                        # mov [log+MAP], ecx
               + b'\x8B\x44\x24\x08'                                      # mov eax, [esp+8] (the key)
               + b'\xA3' + _dword(log + L_KEY)                            # mov [log+KEY], eax
               + b'\xC2\x08\x00')                                         # ret 8
        _patch(h, ERASE,
               b'\x8B\x44\x24\x08'                                        # mov eax, [esp+8] (the node)
               + b'\xA3' + _dword(log + L_ERASE_NODE)
               + b'\x8B\x44\x24\x04'                                      # mov eax, [esp+4] (the out slot)
               + b'\x8B\x10'                                              # mov edx, [eax]
               + b'\x89\x15' + _dword(log + L_ERASE_SLOT)
               + b'\x89\x0D' + _dword(log + L_ERASE_MAP)
               + b'\xC2\x08\x00')                                         # ret 8

        release = h.alloc(24, b'\x8B\x44\x24\x04'                         # mov eax, [esp+4] (the flag)
                          + b'\xA3' + _dword(log + L_REL_FLAG)
                          + b'\x89\x0D' + _dword(log + L_REL_OBJ)         # mov [log+REL_OBJ], ecx
                          + b'\xC2\x04\x00')                              # ret 4
        vtable = h.alloc(0x80, bytes(0x80))
        h.uc.mem_write(vtable + 0x74, _dword(release))
        obj = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(obj, _dword(vtable))
        node = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(node + 0x24, _dword(obj))
        bare = h.alloc(0x40, bytes(0x40))
        sentinel = h.alloc(0x40, bytes(0x40))
        manager = h.alloc(0x40, bytes(0x40))
        name = h.alloc(0x1c, bytes(0x1c))
        h.uc.mem_write(name + 4, b'abc\0' + bytes(12))
        h.uc.mem_write(name + 0x14, _dword(3) + _dword(15))
        heap_base = h.heap_ptr

        for label, nodeval, guard, patched in (('erased', node, 0xDEADBEEF, False),
                                               ('bare', bare, 0xDEADBEEF, False),
                                               ('end node', sentinel, sentinel, True)):
            def setup(nv=nodeval, g=guard):
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(log + L_NODE, _dword(nv))
                h.uc.mem_write(manager, bytes(0x40))
                h.uc.mem_write(manager + 0xC, _dword(g))

            h.heap_ptr = heap_base
            setup()
            if patched:
                _patch(h, THROW, b'\x31\xC0\xC2\x08\x00')               # xor eax, eax; ret 8
            diffs = h.compare(THIS, args=[name], regs={UC_X86_REG_ECX: manager}, ret=None)
            if diffs:
                return ['%s: %s' % (label, d) for d in diffs]
            h.heap_ptr = heap_base
            setup()
            res = h.call(THIS, args=[name], regs={UC_X86_REG_ECX: manager})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (label, res['fault'])]
            if res['esp'] != 8:
                return ['%s: stack delta %d, not 8' % (label, res['esp'])]
            if _u32(h, log + L_MAP) != manager + 4 or _u32(h, log + L_KEY) != name:
                return ['%s: the lookup saw %08X %08X' % (label, _u32(h, log + L_MAP), _u32(h, log + L_KEY))]
            if _u32(h, log + L_ERASE_MAP) != manager + 4:
                return ['%s: the erase saw map %08X' % (label, _u32(h, log + L_ERASE_MAP))]
            if _u32(h, log + L_ERASE_NODE) != nodeval or _u32(h, log + L_ERASE_SLOT) != nodeval:
                return ['%s: the erase saw node %08X slot %08X'
                        % (label, _u32(h, log + L_ERASE_NODE), _u32(h, log + L_ERASE_SLOT))]
            if label == 'erased':
                if _u32(h, log + L_REL_OBJ) != obj or _u32(h, log + L_REL_FLAG) != 1:
                    return ['erased: the release saw %08X flag %d'
                            % (_u32(h, log + L_REL_OBJ), _u32(h, log + L_REL_FLAG))]
            elif _u32(h, log + L_REL_OBJ) != 0:
                return ['%s: an object was released (%08X)' % (label, _u32(h, log + L_REL_OBJ))]
        h.uc.mem_write(THROW, saved[THROW])
        h.uc.ctl_remove_cache(THROW, THROW + 6)

        # the real throw: the replacement must end the run there, with the lookup done and nothing erased
        h.heap_ptr = heap_base
        h.uc.mem_write(log, bytes(LOG_SIZE))
        h.uc.mem_write(log + L_NODE, _dword(sentinel))
        h.uc.mem_write(manager, bytes(0x40))
        h.uc.mem_write(manager + 0xC, _dword(sentinel))
        res = h.call(THIS, args=[name], regs={UC_X86_REG_ECX: manager})
        if res['fault'] != 'threw':
            return ['throw: fault %r, not threw' % (res['fault'],)]
        if _u32(h, log + L_MAP) != manager + 4 or _u32(h, log + L_KEY) != name:
            return ['throw: the lookup saw %08X %08X' % (_u32(h, log + L_MAP), _u32(h, log + L_KEY))]
        if _u32(h, log + L_REL_OBJ) != 0 or _u32(h, log + L_ERASE_NODE) != 0:
            return ['throw: the node was released or erased']
        h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
