"""Link a synthetic image to check BSS placement and references across the split."""
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

import pefile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from exe2obj import IMAGE_REL_I386_DIR32, write_coff


class BssTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('lld-link'), 'lld-link is required')
    def test_unaligned_prefix_and_tail_symbol(self):
        # A 0x600-byte initialized prefix exercises the case where page alignment
        # of the BSS chunk would incorrectly move every symbol in the tail.
        sections = [
            ['.text', 0, 1, bytearray(b'\xc3'), []],
            ['.rdata', 0, 4, bytearray(4), [(0, 2, IMAGE_REL_I386_DIR32)]],
            ['.data', 0, 0x600, bytearray(b'Z' * 0x600), []],
            ['.bss', 0, 0x1900, bytearray(0x1900), []],
        ]
        symbols = [('_start', 0, 1, 2), ('_prefix', 0, 3, 2), ('_tail', 0x1800, 4, 2)]
        with tempfile.TemporaryDirectory() as directory:
            obj = Path(directory) / 'test.obj'
            exe = Path(directory) / 'test.exe'
            write_coff(str(obj), sections, symbols)
            subprocess.run(['lld-link', '/machine:x86', '/subsystem:console', '/entry:start',
                            '/nodefaultlib', '/safeseh:no', '/fixed:no', '/merge:.bss=.data',
                            '/out:' + str(exe), str(obj)], check=True, capture_output=True)
            with pefile.PE(str(exe)) as pe:
                by_name = {s.Name.rstrip(b'\0'): s for s in pe.sections}
                data = by_name[b'.data']
                self.assertEqual(data.Misc_VirtualSize, 0x1f00)
                self.assertEqual(data.SizeOfRawData, 0x600)
                mapped = pe.get_memory_mapped_image()
                start = data.VirtualAddress
                self.assertEqual(mapped[start:start + 0x1f00], b'Z' * 0x600 + bytes(0x1900))
                target = struct.unpack('<I', by_name[b'.rdata'].get_data()[:4])[0]
                self.assertEqual(target, pe.OPTIONAL_HEADER.ImageBase + start + 0x600 + 0x1800)

    def test_nonzero_tail_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                write_coff(str(Path(directory) / 'bad.obj'),
                           [['.bss', 0, 4, bytearray(b'\x01\0\0\0'), []]], [])

    def test_relocation_in_tail_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                write_coff(str(Path(directory) / 'bad.obj'),
                           [['.bss', 0, 4, bytearray(4), [(0, 0, IMAGE_REL_I386_DIR32)]]], [])


if __name__ == '__main__':
    unittest.main()
