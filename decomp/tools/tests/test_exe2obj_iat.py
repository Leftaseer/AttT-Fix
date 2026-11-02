"""A native import operand stays byte-identical and follows later IAT hooks after relinking."""
import pathlib
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ESP

TOOLS = pathlib.Path(__file__).resolve().parents[1]


@unittest.skipUnless(all(shutil.which(t) for t in ('clang', 'lld-link', 'llvm-dlltool')), 'LLVM required')
class FunctionIatTests(unittest.TestCase):
    def test_native_call_uses_retargeted_canonical_iat(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)

            def run(*command):
                result = subprocess.run([str(x) for x in command], cwd=root, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            (root / 'test.def').write_text('LIBRARY test.dll\nEXPORTS\n Call\n')
            (root / 'entry.s').write_text('.text\n.globl _entry\n_entry:\n calll *__imp__Call\n retl\n')
            run('llvm-dlltool', '-m', 'i386', '-d', 'test.def', '-l', 'test.lib')
            run('clang', '--target=i686-pc-windows-msvc', '-c', 'entry.s', '-o', 'entry.obj')
            run('lld-link', '/entry:entry', '/subsystem:console', '/nodefaultlib', '/fixed:no',
                '/safeseh:no', '/base:0x400000', '/out:original.exe', 'entry.obj', 'test.lib')
            run(sys.executable, '-I', TOOLS / 'exe2obj.py', root / 'original.exe', root / 'relink',
                '--keep-function-iat')
            run('llvm-dlltool', '-m', 'i386', '-d', root / 'relink/imports/test.def', '-l', 'relinked.lib')
            options = (root / 'relink/link.rsp').read_text().split()
            run('lld-link', *options, '/out:rebuilt.exe', '/map:rebuilt.map', root / 'relink/orig.obj', 'relinked.lib')
            run(sys.executable, '-I', TOOLS / 'verify_relink.py', root / 'original.exe', root / 'rebuilt.exe',
                root / 'rebuilt.map', '--keep-function-iat')

            with pefile.PE(str(root / 'original.exe')) as original, pefile.PE(str(root / 'rebuilt.exe')) as rebuilt:
                base = rebuilt.OPTIONAL_HEADER.ImageBase
                entry = original.OPTIONAL_HEADER.AddressOfEntryPoint
                old_slot = original.DIRECTORY_ENTRY_IMPORT[0].imports[0].address
                new_slot = rebuilt.DIRECTORY_ENTRY_IMPORT[0].imports[0].address
                self.assertEqual(original.get_data(entry, 7), rebuilt.get_data(entry, 7))
                image = rebuilt.get_memory_mapped_image()
                forward = struct.unpack_from('<I', image, old_slot - base)[0]
                self.assertEqual(image[forward - base:forward - base + 2], b'\xff\x25')
                self.assertEqual(struct.unpack_from('<I', image, forward - base + 2)[0], new_slot)

                uc = Uc(UC_ARCH_X86, UC_MODE_32)
                uc.mem_map(base, (len(image) + 0xFFF) & ~0xFFF)
                uc.mem_write(base, image)
                scratch = 0x10000000
                uc.mem_map(scratch, 0x2000)
                stop, stack = scratch + 0x100, scratch + 0x1FF0
                for index, value in enumerate((123, 456)):
                    function = scratch + 0x200 + index * 0x10
                    uc.mem_write(function, b'\xb8' + struct.pack('<I', value) + b'\xc3')
                    uc.mem_write(new_slot, struct.pack('<I', function))
                    uc.mem_write(stack, struct.pack('<I', stop))
                    uc.reg_write(UC_X86_REG_ESP, stack)
                    uc.emu_start(base + entry, stop, count=100)
                    self.assertEqual(uc.reg_read(UC_X86_REG_EAX), value)


if __name__ == '__main__':
    unittest.main()
