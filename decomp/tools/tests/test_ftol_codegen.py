"""Compile generated helper macros and exercise their actual x86 conversions."""
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EDX, UC_X86_REG_ESP

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
from autodecomp import ftol_macro


@unittest.skipUnless(shutil.which('clang') and shutil.which('lld-link'), 'LLVM tools required')
class FtolCodegenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.directory.cleanup)
        root = Path(cls.directory.name)
        src, obj, dll = (root / name for name in ('test.c', 'test.obj', 'test.dll'))
        src.write_text('#include "ghidra_prelude.h"\nint _fltused = 0;\n' +
                       ftol_macro('005E3FA0', 'int') + '\n' +
                       ftol_macro('005E3FD6', 'long long') + '\n' +
                       '__declspec(dllexport) unsigned int column(double v) { return (uint)sub_005E3FA0(v); }\n' +
                       '__declspec(dllexport) long long wide(double v) { return sub_005E3FD6(v); }\n')
        subprocess.run(['clang', '--target=i686-pc-windows-msvc', '-O1', '-march=pentium-mmx',
                        '-mfpmath=387', '-ffreestanding', '-std=gnu11', '-I',
                        str(TOOLS.parent / 'rebuild/include'), '-c', str(src), '-o', str(obj)],
                       check=True, capture_output=True)
        subprocess.run(['lld-link', '/dll', '/noentry', '/nodefaultlib', '/machine:x86',
                        '/safeseh:no', '/out:' + str(dll), str(obj)], check=True, capture_output=True)
        with pefile.PE(str(dll)) as pe:
            cls.base = pe.OPTIONAL_HEADER.ImageBase
            cls.image = pe.get_memory_mapped_image()
            cls.entries = {s.name.decode(): cls.base + s.address for s in pe.DIRECTORY_ENTRY_EXPORT.symbols}

    def call(self, name, value):
        uc = Uc(UC_ARCH_X86, UC_MODE_32)
        uc.mem_map(self.base, (len(self.image) + 0xfff) & ~0xfff)
        uc.mem_write(self.base, self.image)
        stop, stack = 0x0fff0000, 0x30000000
        uc.mem_map(stop, 0x1000)
        uc.mem_map(stack, 0x1000)
        sp = stack + 0x800
        uc.mem_write(sp, struct.pack('<Id', stop, value))
        uc.reg_write(UC_X86_REG_ESP, sp)
        uc.emu_start(self.entries[name], stop, count=1000)
        self.assertEqual(uc.reg_read(UC_X86_REG_ESP), sp + 4)
        return uc.reg_read(UC_X86_REG_EAX) | (uc.reg_read(UC_X86_REG_EDX) << 32 if name == 'wide' else 0)

    def test_signed_conversion_before_unsigned_storage(self):
        for value, expected in [(0.0, 0), (1.9, 1), (-1.9, 0xffffffff),
                                (2147483647.0, 0x7fffffff), (2147483648.0, 0x80000000),
                                (-2147483649.0, 0x80000000), (2.0 ** 96, 0x80000000),
                                (float('inf'), 0x80000000), (float('nan'), 0x80000000)]:
            with self.subTest(value=value):
                self.assertEqual(self.call('column', value), expected)

    def test_64_bit_helper_keeps_its_width(self):
        self.assertEqual(self.call('wide', 2.0 ** 33), 1 << 33)


if __name__ == '__main__':
    unittest.main()
