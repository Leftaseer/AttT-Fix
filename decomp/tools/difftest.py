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


_S = '?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@'
STRING_ALIAS = {
    '??0' + _S + 'QAE@XZ': 'str_ctor', '??0' + _S + 'QAE@PBD@Z': 'str_ctor_cstr', '??0' + _S + 'QAE@ABV01@@Z': 'str_ctor_copy',
    '??1' + _S + 'QAE@XZ': 'str_dtor', '??4' + _S + 'QAEAAV01@ABV01@@Z': 'str_assign',
    '??4' + _S + 'QAEAAV01@PBD@Z': 'str_assign_cstr', '?c_str@' + _S[2:] + 'QBEPBDXZ': 'str_cstr',
    '?size@' + _S[2:] + 'QBEIXZ': 'str_size', '?length@' + _S[2:] + 'QBEIXZ': 'str_size',
}


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
        alias = {'??2@YAPAXI@Z': 'new', '??3@YAXPAX@Z': 'free_like', '??_V@YAXPAX@Z': 'free_like', '??_U@YAPAXI@Z': 'new',
                 '_strnicmp': 'strnicmp', '_stricmp': 'stricmp', '_strlwr': 'strlwr'}
        alias.update(STRING_ALIAS)
        f = getattr(self, 'crt_' + alias.get(name, name.lstrip('_')), None)
        if f is None:
            uc.emu_stop()
            self.fault = 'unsupported import %s!%s' % (dll, name)
            return
        f()

    # --- std::string of MSVCP80 (VC8 layout, 28 bytes: allocator, 16-byte buffer or pointer, size, capacity)
    def _ecx(self):
        return self.uc.reg_read(UC_X86_REG_ECX)

    def _str_get(self, p):
        size, res = struct.unpack('<II', self.uc.mem_read(p + 20, 8))
        if size > 0x100000:
            raise ValueError('bad string')
        data = self.uc.mem_read(p + 4, 4)
        ptr = (p + 4) if res < 16 else struct.unpack('<I', data)[0]
        return bytes(self.uc.mem_read(ptr, size))

    def _str_set(self, p, b):
        if len(b) < 16:
            self.uc.mem_write(p + 4, b + b'\0' * (16 - len(b)))
            res = 15
        else:
            q = self.alloc(len(b) + 1, b + b'\0')
            self.uc.mem_write(p + 4, struct.pack('<I', q))
            res = len(b)
        self.uc.mem_write(p + 20, struct.pack('<II', len(b), res))

    def _str_op(self, fn, pop, ret_this=True):
        try:
            this = self._ecx()
            r = fn(this)
        except (ValueError, UcError):
            self.uc.emu_stop(); self.fault = 'bad std::string'; return
        self._ret(this if ret_this else r, pop)

    def crt_str_ctor(self): self._str_op(lambda t: self._str_set(t, b''), 0)
    def crt_str_ctor_cstr(self): self._str_op(lambda t: self._str_set(t, self._cstr(self._arg(0))), 4)
    def crt_str_ctor_copy(self): self._str_op(lambda t: self._str_set(t, self._str_get(self._arg(0))), 4)
    def crt_str_dtor(self): self._str_op(lambda t: None, 0)
    def crt_str_assign(self): self._str_op(lambda t: self._str_set(t, self._str_get(self._arg(0))), 4)
    def crt_str_assign_cstr(self): self._str_op(lambda t: self._str_set(t, self._cstr(self._arg(0))), 4)
    def crt_str_cstr(self):
        self._str_op(lambda t: (t + 4) if struct.unpack('<I', self.uc.mem_read(t + 24, 4))[0] < 16
                     else struct.unpack('<I', self.uc.mem_read(t + 4, 4))[0], 0, ret_this=False)
    def crt_str_size(self):
        self._str_op(lambda t: struct.unpack('<I', self.uc.mem_read(t + 20, 4))[0], 0, ret_this=False)

    def crt_strcspn(self):
        a, b = self._cstr(self._arg(0)), set(self._cstr(self._arg(1)))
        n = 0
        while n < len(a) and a[n] not in b:
            n += 1
        self._ret(n)

    def crt_memmove_s(self):
        d, dn, src, n = (self._arg(i) for i in range(4))
        if n > dn:
            self._ret(22); return
        self.uc.mem_write(d, bytes(self.uc.mem_read(src, n)))
        self._ret(0)

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


    # operator new/delete, more of the C runtime
    def crt_free_like(self):
        self._ret(0)
    def crt_new(self):
        self._ret(self.alloc(max(1, self._arg(0))))
    def crt_calloc(self):
        n = self._arg(0) * self._arg(1)
        self._ret(self.alloc(max(1, n), bytes(n)))
    def crt_realloc(self):
        p, n = self._arg(0), self._arg(1)
        q = self.alloc(max(1, n))
        if p:
            self.uc.mem_write(q, bytes(self.uc.mem_read(p, n)))
        self._ret(q)
    def crt_memcmp(self):
        a, b, n = self._arg(0), self._arg(1), self._arg(2)
        x, y = bytes(self.uc.mem_read(a, n)), bytes(self.uc.mem_read(b, n))
        self._ret(0 if x == y else (-1 if x < y else 1))
    def crt_memchr(self):
        p, c, n = self._arg(0), self._arg(1) & 0xFF, self._arg(2)
        d = bytes(self.uc.mem_read(p, n)); i = d.find(bytes([c]))
        self._ret(0 if i < 0 else p + i)
    def crt_strcpy(self):
        d, s_ = self._arg(0), self._cstr(self._arg(1))
        self.uc.mem_write(d, s_ + b'\0'); self._ret(d)
    def crt_strncpy(self):
        d, s_, n = self._arg(0), self._cstr(self._arg(1)), self._arg(2)
        self.uc.mem_write(d, (s_ + bytes(n))[:n]); self._ret(d)
    def crt_strcat(self):
        d = self._arg(0); a_ = self._cstr(d); b_ = self._cstr(self._arg(1))
        self.uc.mem_write(d + len(a_), b_ + b'\0'); self._ret(d)
    def crt_strncat(self):
        d = self._arg(0); a_ = self._cstr(d); b_ = self._cstr(self._arg(1))[:self._arg(2)]
        self.uc.mem_write(d + len(a_), b_ + b'\0'); self._ret(d)
    def crt_strchr(self):
        p = self._arg(0); s_ = self._cstr(p); c = self._arg(1) & 0xFF
        i = (s_ + b'\0').find(bytes([c])); self._ret(0 if i < 0 else p + i)
    def crt_strrchr(self):
        p = self._arg(0); s_ = self._cstr(p); c = self._arg(1) & 0xFF
        i = (s_ + b'\0').rfind(bytes([c])); self._ret(0 if i < 0 else p + i)
    def crt_strstr(self):
        p = self._arg(0); a_ = self._cstr(p); b_ = self._cstr(self._arg(1))
        i = a_.find(b_); self._ret(0 if i < 0 else p + i)
    def crt_strncmp(self):
        n = self._arg(2); a_ = self._cstr(self._arg(0))[:n]; b_ = self._cstr(self._arg(1))[:n]
        self._ret((a_ > b_) - (a_ < b_))
    def crt_strnicmp(self):
        n = self._arg(2); a_ = self._cstr(self._arg(0))[:n].lower(); b_ = self._cstr(self._arg(1))[:n].lower()
        self._ret((a_ > b_) - (a_ < b_))
    def crt_stricmp(self):
        a_ = self._cstr(self._arg(0)).lower(); b_ = self._cstr(self._arg(1)).lower()
        self._ret((a_ > b_) - (a_ < b_))
    def crt_strlwr(self):
        p = self._arg(0); self.uc.mem_write(p, self._cstr(p).lower()); self._ret(p)
    def crt_atoi(self):
        import re as _re
        m = _re.match(rb'\s*([+-]?\d+)', self._cstr(self._arg(0)))
        self._ret(int(m.group(1)) & 0xFFFFFFFF if m else 0)
    def crt_tolower(self):
        c = self._arg(0) & 0xFFFFFFFF; self._ret(c + 32 if 65 <= c <= 90 else c)
    def crt_toupper(self):
        c = self._arg(0) & 0xFFFFFFFF; self._ret(c - 32 if 97 <= c <= 122 else c)
    def _ctype(self, f):
        c = self._arg(0)
        self._ret(1 if 0 <= c < 128 and f(chr(c)) else 0)
    def crt_isdigit(self): self._ctype(str.isdigit)
    def crt_isalpha(self): self._ctype(str.isalpha)
    def crt_isspace(self): self._ctype(lambda ch: ch in ' \t\n\r\v\f')
    def crt_isalnum(self): self._ctype(str.isalnum)
    def crt_isupper(self): self._ctype(str.isupper)
    def crt_islower(self): self._ctype(str.islower)
    def crt_ldiv(self):
        # ldiv_t returned in EDX:EAX (quot, rem), truncating division
        n = struct.unpack('<i', struct.pack('<I', self._arg(0)))[0]; d = struct.unpack('<i', struct.pack('<I', self._arg(1)))[0]
        if d == 0:
            self.uc.emu_stop(); self.fault = 'division by zero in ldiv'; return
        q = abs(n) // abs(d) * (1 if (n >= 0) == (d >= 0) else -1); r = n - q * d
        self.uc.reg_write(UC_X86_REG_EDX, r & 0xFFFFFFFF)
        self._ret(q & 0xFFFFFFFF)
    RAND_STATE = 0x0FFF0F00            # inside the STOP page: part of no snapshot, reset per call
    def crt_srand(self):
        self.uc.mem_write(self.RAND_STATE, struct.pack('<I', self._arg(0))); self._ret(0)
    def crt_rand(self):
        st = struct.unpack('<I', self.uc.mem_read(self.RAND_STATE, 4))[0]
        st = (st * 214013 + 2531011) & 0xFFFFFFFF
        self.uc.mem_write(self.RAND_STATE, struct.pack('<I', st))
        self._ret((st >> 16) & 0x7FFF)
    def _cdbl(self, i):
        sp = self.uc.reg_read(UC_X86_REG_ESP)
        return struct.unpack('<d', self.uc.mem_read(sp + 4 + 8 * i, 8))[0]
    def _ret_double(self, v):
        self._ret(None, 0, v)
    def crt_floor(self): self._ret_double(math.floor(self._cdbl(0)))
    def crt_ceil(self): self._ret_double(math.ceil(self._cdbl(0)))
    def crt_sqrt(self): self._ret_double(math.sqrt(self._cdbl(0)) if self._cdbl(0) >= 0 else float('nan'))
    def crt_pow(self):
        try: v = math.pow(self._cdbl(0), self._cdbl(1))
        except (ValueError, OverflowError): v = float('nan')
        self._ret_double(v)
    def _x87_binary(self, fn):
        # st1 op st0 -> st0 (both popped, result pushed)
        y = self._st0()
        self.uc.mem_write(STOP + 0x200, b'\xdd\xd8\xf4')
        eip = self.uc.reg_read(UC_X86_REG_EIP)
        self.uc.emu_start(STOP + 0x200, STOP + 0x202)
        x = self._st0()
        self.uc.emu_start(STOP + 0x200, STOP + 0x202)
        self.uc.reg_write(UC_X86_REG_EIP, eip)
        try: v = fn(x, y)
        except (ValueError, OverflowError, ZeroDivisionError): v = float('nan')
        self._ret(None, 0, v)
    def crt_CIpow(self): self._x87_binary(math.pow)
    def crt_CIatan2(self): self._x87_binary(math.atan2)
    def crt_CIfmod(self): self._x87_binary(math.fmod)
    def crt_CIacos(self): self._x87_unary(lambda v: math.acos(v) if -1 <= v <= 1 else float('nan'))
    def crt_CIasin(self): self._x87_unary(lambda v: math.asin(v) if -1 <= v <= 1 else float('nan'))
    def crt_CIatan(self): self._x87_unary(math.atan)
    def crt_CItan(self): self._x87_unary(math.tan)
    def crt_CIexp(self): self._x87_unary(lambda v: math.exp(v) if v < 700 else float('inf'))
    def crt_CIlog(self): self._x87_unary(lambda v: math.log(v) if v > 0 else float('nan'))
    def crt_CIlog10(self): self._x87_unary(lambda v: math.log10(v) if v > 0 else float('nan'))

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
        uc.mem_write(self.RAND_STATE, struct.pack('<I', 1))      # srand(1): the same rand() sequence for both runs
        try:
            uc.emu_start(entry, STOP, count=getattr(self, 'steps', 5_000_000))
        except UcError as e:
            self.fault = 'fault %s at %08X' % (e, uc.reg_read(UC_X86_REG_EIP))
        eip = uc.reg_read(UC_X86_REG_EIP)
        if self.fault is None and eip != STOP:
            self.fault = 'did not return (EIP %08X)' % eip
        res = {'eax': uc.reg_read(UC_X86_REG_EAX), 'edx': uc.reg_read(UC_X86_REG_EDX), 'ecx': uc.reg_read(UC_X86_REG_ECX),
               'esp': uc.reg_read(UC_X86_REG_ESP) - sp, 'fault': self.fault,
               'ebx': uc.reg_read(UC_X86_REG_EBX), 'esi': uc.reg_read(UC_X86_REG_ESI),
               'edi': uc.reg_read(UC_X86_REG_EDI), 'ebp': uc.reg_read(UC_X86_REG_EBP)}
        try:
            res['st0'] = self._st0()
        except UcError:
            res['st0'] = None
        return res

    def game_address(self, attt_addr):
        """AttT address -> address in the game under test (Valkyrie through symbols/attt2valk.tsv)"""
        if self.orig.pe.FILE_HEADER.TimeDateStamp != 0x4883FB4F:
            return attt_addr
        if not hasattr(self, '_fmap'):
            self._fmap = {}
            for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'symbols', 'attt2valk.tsv')):
                q = l.split('\t')
                self._fmap[int(q[0], 16)] = int(q[1], 16)
        return self._fmap[attt_addr]

    def clobbered(self, va):
        """volatile registers the original may change (symbols/<game>_functions.tsv)"""
        if not hasattr(self, '_clob'):
            game = 'valk' if self.orig.pe.FILE_HEADER.TimeDateStamp == 0x4883FB4F else 'attt'
            self._clob = {}
            for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'symbols', game + '_functions.tsv')):
                if l[0] != '#':
                    q = l.rstrip('\n').split('\t')
                    self._clob[int(q[0], 16)] = set(x.lower() for x in q[4].split(',') if x)
        return self._clob.get(va, {'eax', 'ecx', 'edx'})

    def compare(self, attt_addr, args=(), regs=None, setup=None, ret='eax', mem=True, game_addr=None, check_st0=None):
        """Run original and replacement from the same state; return a list of differences (empty = equal).
        ret: registers holding the result ('eax', 'eax:edx', 'al', 'st0' or None for void); volatile registers
        the original leaves unchanged are compared as well (callers compiled with /LTCG may rely on them)."""
        if check_st0 is not None and ret == 'eax':
            ret = 'eax' if not check_st0 else 'eax'

        va = game_addr if game_addr is not None else self.game_address(attt_addr)
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
        keys = ['fault', 'esp', 'ebx', 'esi', 'edi', 'ebp']
        keys += [r for r in ('eax', 'ecx', 'edx') if r not in self.clobbered(va)]
        if ret in ('eax', 'eax:edx'):
            keys.append('eax')
        if ret == 'eax:edx':
            keys.append('edx')
        for k in dict.fromkeys(keys):
            if r1.get(k) != r2.get(k):
                diffs.append('%s: orig %r new %r' % (k, r1.get(k), r2.get(k)))
        if ret == 'al' and (r1['eax'] & 0xFF) != (r2['eax'] & 0xFF):
            diffs.append('al: orig %r new %r' % (r1['eax'] & 0xFF, r2['eax'] & 0xFF))
        if ret == 'st0' and r1['st0'] != r2['st0'] and not (r1['st0'] != r1['st0'] and r2['st0'] != r2['st0']):
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
