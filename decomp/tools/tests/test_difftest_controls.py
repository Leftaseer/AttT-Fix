"""Link small x86 programs with known defects and require the real differential harness to detect them."""
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from difftest import HEAP, HEAP_SIZE, Harness
from autoverify import FastHarness, NativeCoverage
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESP
from exe2obj import write_coff, IMAGE_REL_I386_DIR32


@unittest.skipUnless(all(shutil.which(t) for t in ('lld-link', 'llvm-dlltool')), 'LLVM linker required')
class HarnessControlTests(unittest.TestCase):
    ENTRY = 0x401000
    VALUE = 0x403000

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / 'control.def').write_text('LIBRARY control.dll\nEXPORTS\n Probe\n')
        self.run_tool('llvm-dlltool', '-m', 'i386', '-d', 'control.def', '-l', 'control.lib')

    def run_tool(self, *command):
        result = subprocess.run([str(x) for x in command], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def harness(self, original, replacement, harness_type=Harness):
        code = bytearray(b'\xCC' * 0x200)
        code[:len(original)] = original
        code[0x100:0x100 + len(replacement)] = replacement
        for kind in ('original', 'rebuilt'):
            text = code[:]
            if kind == 'rebuilt':
                text[:5] = b'\xE9' + struct.pack('<i', 0x100 - 5)
            sections = [
                ['.text', 0, len(text), text, []],
                ['.rdata', 0, 4, bytearray(4), [(0, 1, IMAGE_REL_I386_DIR32)]],
                ['.data', 0, 16, bytearray(16), []],
            ]
            symbols = [('_entry', 0, 1, 2), ('__imp__Probe', 0, 0, 2)]
            write_coff(str(self.root / (kind + '.obj')), sections, symbols)
            self.run_tool('lld-link', '/entry:entry', '/base:0x400000', '/subsystem:console', '/nodefaultlib',
                          '/safeseh:no', '/fixed:no', '/out:' + kind + '.exe', '/map:' + kind + '.map',
                          kind + '.obj', 'control.lib')
        return harness_type(str(self.root / 'original.exe'), str(self.root / 'rebuilt.exe'), str(self.root / 'rebuilt.map'))

    def test_equal_implementations_pass(self):
        code = bytes.fromhex('b801000000 c3')
        self.assertEqual(self.harness(code, code).compare(self.ENTRY), [])

    def test_original_entry_restores_the_entire_instruction_crossed_by_the_jump(self):
        code = b'\x90\x8b\x05' + struct.pack('<I', self.VALUE) + b'\xc3'
        h = self.harness(code, code)
        h.uc.mem_write(self.VALUE, struct.pack('<I', 7))
        h.uc.mem_write(self.ENTRY + 5, b'\0\0')
        self.assertEqual(h.compare(self.ENTRY), [])
        self.assertEqual(h.uc.mem_read(self.ENTRY + 5, 2), b'\0\0')

    def test_wrong_return_is_detected(self):
        h = self.harness(bytes.fromhex('b801000000 c3'), bytes.fromhex('b802000000 c3'))
        observed = []
        h.comparison_observer = lambda *result: observed.append(result)
        self.assertTrue(any('eax:' in d for d in h.compare(self.ENTRY)))
        self.assertEqual(observed[0][0], self.ENTRY)
        self.assertTrue(observed[0][3])

    def test_missing_memory_write_is_detected(self):
        original = b'\xC7\x05' + struct.pack('<II', self.VALUE, 7) + bytes.fromhex('b801000000 c3')
        h = self.harness(original, bytes.fromhex('b801000000 c3'))
        self.assertTrue(any('memory differs' in d for d in h.compare(self.ENTRY)))

    def test_callee_saved_register_corruption_is_detected(self):
        h = self.harness(bytes.fromhex('b801000000 c3'), bytes.fromhex('31db b801000000 c3'))
        self.assertTrue(any('ebx:' in d for d in h.compare(self.ENTRY)))

    def test_wrong_stack_cleanup_is_detected(self):
        h = self.harness(bytes.fromhex('b801000000 c3'), bytes.fromhex('b801000000 c20400'))
        self.assertTrue(any('esp:' in d for d in h.compare(self.ENTRY, args=[123])))

    def test_wrong_float_result_is_detected(self):
        h = self.harness(bytes.fromhex('d9e8 90 90 90 c3'), bytes.fromhex('d9ee c3'))
        self.assertTrue(any('st0:' in d for d in h.compare(self.ENTRY, ret='st0')))

    def test_boolean_result_ignores_unused_upper_bytes(self):
        h = self.harness(bytes.fromhex('b801010000 c3'), bytes.fromhex('b801020000 c3'))
        self.assertEqual(h.compare(self.ENTRY, ret='al'), [])
        self.assertTrue(h.compare(self.ENTRY, ret='eax'))

    def test_fault_only_blocks_do_not_count_as_normal_coverage(self):
        self.check_fault_only_coverage()

    @unittest.skipUnless(shutil.which('cc') or shutil.which('clang'), 'C compiler required')
    def test_native_coverage_matches_python_on_fault_and_normal_return(self):
        source = Path(__file__).resolve().parents[1] / 'sweep_coverage.c'
        library = self.root / 'sweep_coverage.so'
        self.run_tool(shutil.which('cc') or shutil.which('clang'), '-O3', '-shared', '-fPIC',
                      '-ffreestanding', '-nostdlib', source, '-o', library)
        self.assertEqual(self.check_fault_only_coverage(str(library)), self.check_fault_only_coverage())

        engine = Uc(UC_ARCH_X86, UC_MODE_32)
        start, blocks = 0x1000, 180
        stop = start + 2 * blocks
        engine.mem_map(start, 0x1000)
        engine.mem_write(start, b'\xeb\0' * blocks)
        coverage = NativeCoverage(engine, str(library))
        coverage.begin(start, stop)
        engine.emu_start(start, stop)
        self.assertEqual(coverage.end(start), {(start + 2 * i, 2) for i in range(blocks)})

    def check_fault_only_coverage(self, library=None):
        code = bytes.fromhex('85c9 7406 a10000adde c3 b801000000 c3')
        h = self.harness(code, code, FastHarness)
        h.setup_regions(library)
        h.cov_lo, h.cov_hi = self.ENTRY, self.ENTRY + len(code)
        h.new_head = bytes(h.uc.mem_read(self.ENTRY, len(code)))
        first, second = h.run_case(self.ENTRY, code, [], {UC_X86_REG_ECX: 0}, 'eax', 0, self.ENTRY)
        self.assertIsNone(first[0]['fault'])
        self.assertIsNone(second[0]['fault'])
        successful = h.normal_cov.copy()
        first, second = h.run_case(self.ENTRY, code, [], {UC_X86_REG_ECX: 1}, 'eax', 0, self.ENTRY)
        self.assertIsNotNone(first[0]['fault'])
        self.assertIsNotNone(second[0]['fault'])
        self.assertEqual(h.normal_cov, successful)
        self.assertGreater(sum(n for _, n in h.cov), sum(n for _, n in h.normal_cov))
        return h.cov, h.normal_cov

    def test_heap_snapshots_capture_guest_and_host_writes_across_pages(self):
        # A guest store crosses the last two heap pages, well beyond the input allocator.
        address = HEAP + HEAP_SIZE - 0x1002
        original = b'\xc7\x05' + struct.pack('<II', address, 0x12345678) + b'\xc3'
        replacement = b'\xc3'
        h = self.harness(original, replacement, FastHarness)
        h.setup_regions()
        h.cov_lo, h.cov_hi = self.ENTRY, self.ENTRY + len(original)
        h.new_head = bytes(h.uc.mem_read(self.ENTRY, len(original)))
        h.uc.mem_write(address, b'abcdefgh')

        def write_in_import(uc, pc, size, user):
            uc.mem_write(address + 2, b'XY')

        h.uc.hook_add(UC_HOOK_CODE, write_in_import, begin=self.ENTRY + 0x100, end=self.ENTRY + 0x100)
        (_, first), (_, second) = h.run_case(self.ENTRY, original, [], {}, None, 0, self.ENTRY)
        offset = address - HEAP
        self.assertEqual(first[-2][offset:offset + 8], b'xV4\x12efgh')
        self.assertEqual(second[-2][offset:offset + 8], b'abXYefgh')
        self.assertEqual(bytes(h.uc.mem_read(address, 8)), b'abcdefgh')


class ImportModelTests(unittest.TestCase):
    ENTRY, STOP = 0x1000, 0x1100
    SP = 0x1800
    LEFT, RIGHT = 0x2000, 0x2040
    SWAP = '?swap@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEXAAV12@@Z'

    def setUp(self):
        self.h = Harness.__new__(Harness)
        self.uc = self.h.uc = Uc(UC_ARCH_X86, UC_MODE_32)
        self.uc.mem_map(self.ENTRY, 0x2000)
        self.uc.mem_write(self.ENTRY, b'\xc3')
        self.uc.hook_add(UC_HOOK_CODE, self.h._on_import, begin=self.ENTRY, end=self.ENTRY)

    def call(self, dll, name, args, this=0):
        self.h.imp_by_addr = {self.ENTRY: (dll, name)}
        self.h.fault = None
        self.uc.reg_write(UC_X86_REG_ECX, this)
        self.uc.reg_write(UC_X86_REG_ESP, self.SP)
        self.uc.mem_write(self.SP, struct.pack('<' + 'I' * (len(args) + 1), self.STOP, *args))
        self.uc.emu_start(self.ENTRY, self.STOP, count=2)
        if self.h.fault is None:
            self.assertEqual(self.uc.reg_read(UC_X86_REG_ESP), self.SP + 4 * (1 + len(args)))
        return self.uc.reg_read(UC_X86_REG_EAX)

    def test_string_swap_keeps_allocators_and_moves_the_full_union(self):
        short = b'AAAA' + b'x\0' + b'!' * 14 + struct.pack('<II', 1, 15)
        long = b'BBBB' + struct.pack('<I', 0x2080) + b'?' * 12 + struct.pack('<II', 20, 31)
        heap = b'abcdefghijklmnopqrst\0'
        self.uc.mem_write(self.LEFT, short)
        self.uc.mem_write(self.RIGHT, long)
        self.uc.mem_write(0x2080, heap)
        self.call('msvcp80.dll', self.SWAP, [self.RIGHT], self.LEFT)
        self.assertEqual(self.uc.mem_read(self.LEFT, 28), short[:4] + long[4:])
        self.assertEqual(self.uc.mem_read(self.RIGHT, 28), long[:4] + short[4:])
        self.assertEqual(self.uc.mem_read(0x2080, len(heap)), heap)
        self.call('msvcp80.dll', self.SWAP, [self.LEFT], self.LEFT)
        self.assertEqual(self.uc.mem_read(self.LEFT, 28), short[:4] + long[4:])

    def test_string_swap_rejects_null_and_overlapping_objects(self):
        for other in (0, self.LEFT + 4):
            with self.subTest(other=other):
                self.call('msvcp80.dll', self.SWAP, [other], self.LEFT)
                self.assertIn('unsupported', self.h.fault)

    def test_rectangle_writes_preserve_signed_bits_and_wrap(self):
        for name, args, expected in [
            ('SetRect', [0x7fffffff, 0x80000000, 0xffffffff, 0], (0x7fffffff, -0x80000000, -1, 0)),
            ('OffsetRect', [1, 0xffffffff], (-0x80000000, 0x7fffffff, 0, -1)),
            ('InflateRect', [0xffffffff, 2], (-0x7fffffff, 0x7ffffffd, -1, 1)),
            ('SetRectEmpty', [], (0, 0, 0, 0)),
        ]:
            with self.subTest(name=name):
                self.assertEqual(self.call('user32.dll', name, [self.LEFT, *args]), 1)
                self.assertEqual(struct.unpack('<4i', self.uc.mem_read(self.LEFT, 16)), expected)
                self.assertEqual(self.call('user32.dll', name, [0, *args]), 0)

    def test_point_in_rectangle_uses_signed_half_open_bounds(self):
        self.uc.mem_write(self.LEFT, struct.pack('<4i', -2, -3, 4, 5))
        for x, y, expected in [(-2, -3, 1), (3, 4, 1), (-3, 0, 0), (0, -4, 0), (4, 0, 0), (0, 5, 0)]:
            with self.subTest(x=x, y=y):
                args = [self.LEFT, x & 0xffffffff, y & 0xffffffff]
                self.assertEqual(self.call('user32.dll', 'PtInRect', args), expected)
        self.assertEqual(self.call('user32.dll', 'PtInRect', [0, 0, 0]), 0)


if __name__ == '__main__':
    unittest.main()
