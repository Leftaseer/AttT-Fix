#!/usr/bin/env python3
"""Differential tests of decompiled functions in an x86 emulator (Unicorn).

The rebuilt exe holds both versions of a replaced function: the new code, and the original body behind the
5-byte jmp that build.py placed at its entry.  The harness maps the rebuilt image once, then runs the function
twice from the same memory snapshot: once as original (entry bytes restored from the original exe) and once
through the jmp.  It compares EAX, EDX, ST0 and every byte of writable memory (data, heap, stack).

Imports are emulated by small Python versions of the C runtime functions (CRT_IMPL); a test that reaches any
other import stops with 'unsupported import'.

usage (from a test file):
    from difftest import Harness
    h = Harness(orig_exe, rebuilt_exe, rebuilt_map)
    h.compare(0x004064D0, args=[L], setup=lambda m: ...)      # AttT address of the replaced function
"""
import os, sys, struct, math, re, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import PE
from unicorn import Uc, UcError, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_INVALID, UC_PROT_ALL
from unicorn.x86_const import *

STOP = 0x0FFF0000        # return address of the call under test
IMPBASE = 0x0FE00000     # fake addresses of imported functions
HEAP = 0x20000000
HEAP_SIZE = 0x01000000
STACK = 0x30000000
STACK_SIZE = 0x00100000
TEB = 0x7FFD0000


class Unsupported(Exception):
    pass


class Harness:
    def __init__(self, orig_exe, rebuilt_exe, rebuilt_map):
        self.orig = PE(orig_exe)
        self.rb = PE(rebuilt_exe)
        self.starts = {}
        for l in open(rebuilt_map):
            m = re.search(r'__orig_(\w+)_start\s+([0-9a-fA-F]+)', l)
            if m:
                self.starts['.' + m.group(1)] = int(m.group(2), 16)
        self.uc = Uc(UC_ARCH_X86, UC_MODE_32)
        img = self.rb.pe.get_memory_mapped_image()
        size = (len(img) + 0xFFFF) & ~0xFFFF
        self.uc.mem_map(self.rb.base, size, UC_PROT_ALL)
        self.uc.mem_write(self.rb.base, img)
        self.img_range = (self.rb.base, self.rb.base + size)
        for base, sz in ((HEAP, HEAP_SIZE), (STACK, STACK_SIZE), (IMPBASE, 0x10000), (STOP, 0x1000), (TEB, 0x1000)):
            self.uc.mem_map(base, sz, UC_PROT_ALL)
        self.uc.mem_write(STOP, b'\xf4')
        # TEB: fs:[0] = end of SEH chain, fs:[0x18] = TEB
        self.uc.mem_write(TEB, struct.pack('<I', 0xFFFFFFFF) + b'\0' * 0x14 + struct.pack('<I', TEB))
        self._setup_fs()
        # imports -> fake addresses
        self.imp_by_addr = {}
        k = 0
        for e in self.rb.pe.DIRECTORY_ENTRY_IMPORT:
            for i in e.imports:
                fake = IMPBASE + 16 * k
                k += 1
                self.uc.mem_write(i.address, struct.pack('<I', fake))
                self.uc.mem_write(fake, b'\xc3')
                self.imp_by_addr[fake] = (e.dll.decode().lower(), (i.name or b'ord').decode())
        self.uc.hook_add(UC_HOOK_CODE, self._on_import, begin=IMPBASE, end=IMPBASE + 0x10000)
        self.heap_ptr = HEAP + 0x10

    def _setup_fs(self):
        """flat code/data segments and FS -> TEB through a GDT (SEH frames read fs:[0])"""
        gdt = TEB + 0x800

        def desc(base, limit, access, flags=0xC):
            return struct.pack('<HHBBBB', limit & 0xFFFF, base & 0xFFFF, (base >> 16) & 0xFF, access,
                               ((limit >> 16) & 0xF) | (flags << 4), (base >> 24) & 0xFF)
        table = b'\0' * 8 + desc(0, 0xFFFFF, 0x9B) + desc(0, 0xFFFFF, 0x93) + desc(TEB, 0xFFF, 0x93, 0x4) + desc(0, 0xFFFFF, 0x93)
        self.uc.mem_write(gdt, table)
        self.uc.reg_write(UC_X86_REG_GDTR, (0, gdt, len(table) - 1, 0))
        self.uc.reg_write(UC_X86_REG_SS, 2 << 3)
        self.uc.reg_write(UC_X86_REG_DS, 2 << 3)
        self.uc.reg_write(UC_X86_REG_ES, 2 << 3)
        self.uc.reg_write(UC_X86_REG_FS, 3 << 3)

    # --- addresses
    def to_rebuilt(self, va):
        """original-exe address -> address in the rebuilt image (sections may have moved)"""
        for s in self.orig.pe.sections:
            n = s.Name.rstrip(b'\0').decode()
            v = self.orig.base + s.VirtualAddress
            if n in self.starts and v <= va < v + max(s.Misc_VirtualSize, s.SizeOfRawData):
                return self.starts[n] + va - v
        return va

    def alloc(self, n, data=None):
        p = (self.heap_ptr + 15) & ~15
        self.heap_ptr = p + n
        if data is not None:
            self.uc.mem_write(p, bytes(data))
        return p

    # --- C runtime
    def _arg(self, i):
        sp = self.uc.reg_read(UC_X86_REG_ESP)
        return struct.unpack('<I', self.uc.mem_read(sp + 4 + 4 * i, 4))[0]

    def _ret(self, eax=None, pop=0, st0=None):
        uc = self.uc
        sp = uc.reg_read(UC_X86_REG_ESP)
        ra = struct.unpack('<I', uc.mem_read(sp, 4))[0]
        if eax is not None:
            uc.reg_write(UC_X86_REG_EAX, eax & 0xFFFFFFFF)
        if st0 is not None:
            uc.reg_write(UC_X86_REG_FP0, st0) if False else self._push_st0(st0)
        uc.reg_write(UC_X86_REG_ESP, sp + 4 + pop)
        uc.reg_write(UC_X86_REG_EIP, ra)

    def _push_st0(self, value):
        # fld qword from scratch memory
        scratch = STOP + 0x100
        self.uc.mem_write(scratch, struct.pack('<d', value))
        code = b'\xdd\x05' + struct.pack('<I', scratch) + b'\xf4'
        self.uc.mem_write(STOP + 0x200, code)
        eip = self.uc.reg_read(UC_X86_REG_EIP)
        self.uc.emu_start(STOP + 0x200, STOP + 0x206)
        self.uc.reg_write(UC_X86_REG_EIP, eip)

    def _st0(self):
        scratch = STOP + 0x100
        self.uc.mem_write(STOP + 0x200, b'\xdd\x15' + struct.pack('<I', scratch))   # fst qword [scratch]
        self.uc.emu_start(STOP + 0x200, STOP + 0x206)
        return struct.unpack('<d', self.uc.mem_read(scratch, 8))[0]

    def _cstr(self, p):
        out = bytearray()
        while True:
            b = self.uc.mem_read(p + len(out), 64)
            i = b.find(b'\0')
            if i >= 0:
                return bytes(out + b[:i])
            out += b

    def _on_import(self, uc, addr, size, user):
        dll, name = self.imp_by_addr.get(addr, ('?', '?'))
        f = getattr(self, 'crt_' + name.lstrip('_'), None)
        if f is None:
            uc.emu_stop()
            self.fault = 'unsupported import %s!%s' % (dll, name)
            return
        f()

    def crt_malloc(self):
        self._ret(self.alloc(self._arg(0)))

    def crt_free(self):
        self._ret(0)

    def crt_memcpy(self):
        d, s, n = self._arg(0), self._arg(1), self._arg(2)
        self.uc.mem_write(d, bytes(self.uc.mem_read(s, n)))
        self._ret(d)
    crt_memmove = crt_memcpy

    def crt_memset(self):
        d, c, n = self._arg(0), self._arg(1), self._arg(2)
        self.uc.mem_write(d, bytes([c & 0xFF]) * n)
        self._ret(d)

    def crt_strlen(self):
        self._ret(len(self._cstr(self._arg(0))))

    def crt_strcmp(self):
        a, b = self._cstr(self._arg(0)), self._cstr(self._arg(1))
        self._ret((a > b) - (a < b))

    def _x87_unary(self, fn):
        x = self._st0()
        # pop the argument and push the result: emulate by replacing st0
        self.uc.mem_write(STOP + 0x200, b'\xdd\xd8\xf4')                          # fstp st(0)
        eip = self.uc.reg_read(UC_X86_REG_EIP)
        self.uc.emu_start(STOP + 0x200, STOP + 0x202)
        self.uc.reg_write(UC_X86_REG_EIP, eip)
        self._ret(None, 0, fn(x))

    def crt_CIsin(self): self._x87_unary(math.sin)
    def crt_CIcos(self): self._x87_unary(math.cos)
    def crt_CIsqrt(self): self._x87_unary(math.sqrt)

    # --- running
    def snapshot(self):
        regions = [(self.img_range[0], self.img_range[1] - self.img_range[0]), (HEAP, HEAP_SIZE), (STACK, STACK_SIZE)]
        return [(b, bytes(self.uc.mem_read(b, n))) for b, n in regions]

    def restore(self, snap):
        for b, data in snap:
            self.uc.mem_write(b, data)

    def call(self, entry, args=(), regs=None, fpu_args=()):
        uc = self.uc
        self.fault = None
        sp = STACK + STACK_SIZE - 0x1000
        frame = struct.pack('<I', STOP) + b''.join(struct.pack('<I', a & 0xFFFFFFFF) for a in args)
        sp -= len(frame)
        self.arg_sp = sp + 4 + 4 * len(args)    # argument slots belong to the callee (MSVC reuses them)
        uc.mem_write(sp, frame)
        for r, v in {UC_X86_REG_EAX: 0, UC_X86_REG_ECX: 0, UC_X86_REG_EDX: 0, UC_X86_REG_EBX: 0x0BB0BB0B,
                     UC_X86_REG_ESI: 0x05150515, UC_X86_REG_EDI: 0x0D150D15, UC_X86_REG_EBP: 0x0EB00EB0}.items():
            uc.reg_write(r, v)
        for r, v in (regs or {}).items():
            uc.reg_write(r, v & 0xFFFFFFFF)
        uc.reg_write(UC_X86_REG_ESP, sp)
        try:
            uc.emu_start(entry, STOP, count=5_000_000)
        except UcError as e:
            self.fault = 'fault %s at %08X' % (e, uc.reg_read(UC_X86_REG_EIP))
        eip = uc.reg_read(UC_X86_REG_EIP)
        if self.fault is None and eip != STOP:
            self.fault = 'did not return (EIP %08X)' % eip
        res = {'eax': uc.reg_read(UC_X86_REG_EAX), 'edx': uc.reg_read(UC_X86_REG_EDX),
               'esp': uc.reg_read(UC_X86_REG_ESP) - sp, 'fault': self.fault,
               'ebx': uc.reg_read(UC_X86_REG_EBX), 'esi': uc.reg_read(UC_X86_REG_ESI),
               'edi': uc.reg_read(UC_X86_REG_EDI), 'ebp': uc.reg_read(UC_X86_REG_EBP)}
        try:
            res['st0'] = self._st0()
        except UcError:
            res['st0'] = None
        return res

    def compare(self, attt_addr, args=(), regs=None, setup=None, check_st0=True, mem=True, game_addr=None):
        """Run original and replacement from the same state; return a list of differences (empty = equal)."""
        va = game_addr if game_addr is not None else attt_addr
        entry = self.to_rebuilt(va)
        orig_head = self.orig.read(va, 5)
        new_head = bytes(self.uc.mem_read(entry, 5))
        if new_head[0] != 0xE9:
            raise ValueError('%08X is not replaced in the rebuilt exe' % va)
        heap0 = self.heap_ptr
        if setup:
            setup(self)
        base = self.snapshot()
        hp = self.heap_ptr
        self.uc.mem_write(entry, orig_head)
        r1 = self.call(entry, args, regs)
        self.uc.mem_write(entry, new_head)
        m1 = self.snapshot() if mem else None
        self.restore(base)
        self.heap_ptr = hp
        self.uc.mem_write(entry, new_head)
        r2 = self.call(entry, args, regs)
        m2 = self.snapshot() if mem else None
        self.restore(base)
        self.heap_ptr = heap0
        diffs = []
        for k in ('fault', 'eax', 'edx', 'esp', 'ebx', 'esi', 'edi', 'ebp'):
            if r1[k] != r2[k]:
                diffs.append('%s: orig %r new %r' % (k, r1[k], r2[k]))
        if check_st0 and r1['st0'] != r2['st0'] and not (r1['st0'] != r1['st0'] and r2['st0'] != r2['st0']):
            diffs.append('st0: orig %r new %r' % (r1['st0'], r2['st0']))
        if mem:
            for (b, d1), (_, d2) in zip(m1, m2):
                if b == STACK:      # the callee's own frame below the arguments is scratch
                    keep = STACK + STACK_SIZE - self.arg_sp
                    d1, d2 = d1[-keep:], d2[-keep:]
                    b = self.arg_sp
                if d1 != d2:
                    i = next(j for j in range(len(d1)) if d1[j] != d2[j])
                    diffs.append('memory differs at %08X: orig %s new %s' % (b + i, d1[i:i + 8].hex(), d2[i:i + 8].hex()))
                    break
        return diffs


def run_tests(test_files, orig, rebuilt, mapf):
    h = Harness(orig, rebuilt, mapf)
    total = bad = 0
    for tf in test_files:
        ns = {'h': h, 'random': random, 'struct': struct}
        exec(compile(open(tf).read(), tf, 'exec'), ns)
        for name, fn in ns.items():
            if name.startswith('test_') and callable(fn):
                total += 1
                res = fn(h)
                if res:
                    bad += 1
                    print('FAIL %s:%s\n  %s' % (os.path.basename(tf), name, '\n  '.join(res[:5])))
                else:
                    print('ok   %s:%s' % (os.path.basename(tf), name))
    print('%d tests, %d failed' % (total, bad))
    return bad == 0


if __name__ == '__main__':
    import glob
    orig, rebuilt, mapf = sys.argv[1:4]
    files = sys.argv[4:] or sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rebuild', 'tests', '*.py')))
    sys.exit(0 if run_tests(files, orig, rebuilt, mapf) else 1)
