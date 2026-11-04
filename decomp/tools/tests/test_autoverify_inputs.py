"""Replacement selection and floating-point input policy must not create false verification claims."""
from pathlib import Path
import random
import json
import signal
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import autoverify
from verification_inventory import read_sweep
from verify_sweep import fingerprint_tree, interruption_record


class SelectionTests(unittest.TestCase):
    def test_default_intersects_active_replacements_and_generated_sources(self):
        self.assertEqual(autoverify.select_targets([3, 2, 1, 2], [2, 3, 4]), [2, 3])

    def test_explicit_native_function_is_rejected(self):
        with self.assertRaisesRegex(ValueError, '0044A9C0'):
            autoverify.select_targets([0x44FD50], [0x44FD50, 0x44A9C0], [0x44A9C0])

    def test_mixed_request_is_rejected_as_a_whole(self):
        with self.assertRaises(ValueError):
            autoverify.select_targets([1, 2], [1, 2, 3], [2, 3])

    def test_explicit_selection_is_unique_and_sorted(self):
        self.assertEqual(autoverify.select_targets([1, 2, 3], [1, 2, 3], [3, 1, 3]), [1, 3])


class FloatingInputTests(unittest.TestCase):
    def test_default_keeps_nan_infinity_and_payload_bits(self):
        with patch.object(autoverify, 'NONAN', False):
            for bits in (0x7FC00001, 0x7F800001, 0xFFFFFFFF, 0x7F800000, 0xFF800000, 0x80000000):
                self.assertEqual(autoverify.no_nan(bits), bits)

    def test_finite_only_is_an_explicit_filter(self):
        with patch.object(autoverify, 'NONAN', True):
            for bits in (0x7FC00001, 0x7F800001, 0xFFFFFFFF, 0x7F800000, 0xFF800000):
                self.assertNotEqual((autoverify.no_nan(bits) >> 23) & 0xFF, 0xFF)
            self.assertEqual(autoverify.no_nan(0x80000000), 0x80000000)

    def test_typed_float_arguments_include_nonfinite_and_signed_zero(self):
        with patch.object(autoverify, 'NONAN', False):
            rnd = random.Random(17)
            values = {autoverify.make_arg(None, rnd, 'float', {})[0] for _ in range(256)}
            self.assertIn(0x80000000, values)
            self.assertIn(0x7F800000, values)
            self.assertIn(0xFF800000, values)
            self.assertTrue(any((v & 0x7FFFFFFF) > 0x7F800000 for v in values))

    def test_finite_only_typed_arguments_are_finite(self):
        with patch.object(autoverify, 'NONAN', True):
            rnd = random.Random(17)
            for _ in range(256):
                value = autoverify.make_arg(None, rnd, 'float', {})[0]
                self.assertNotEqual((value >> 23) & 0xFF, 0xFF)


class InterruptionTests(unittest.TestCase):
    def test_timeout_and_emulator_crash_are_distinct(self):
        self.assertEqual(interruption_record('00458380', 3, 20)['status'], 'timeout')
        self.assertEqual(interruption_record('00458380', -signal.SIGSEGV, 20)['status'], 'emulator_crash')

    def test_unknown_interruption_is_not_called_a_crash(self):
        with tempfile.TemporaryDirectory() as root:
            status, _ = autoverify.interruption_details(str(Path(root) / 'run.cur'), 0x458380)
            self.assertEqual(status, 'interrupted')

    def test_reason_must_match_the_interrupted_function(self):
        with tempfile.TemporaryDirectory() as root:
            cur = str(Path(root) / 'run.cur')
            Path(cur + '.reason.json').write_text(json.dumps(interruption_record('00458380', 3, 20)))
            self.assertEqual(autoverify.interruption_details(cur, 0x458380)[0], 'timeout')
            self.assertEqual(autoverify.interruption_details(cur, 0x48C980)[0], 'interrupted')


class InventorySweepTests(unittest.TestCase):
    def setUp(self):
        root = tempfile.TemporaryDirectory()
        self.addCleanup(root.cleanup)
        self.sweep = Path(root.name) / 'sweep'
        self.auto = Path(root.name) / 'auto'
        self.sweep.mkdir()
        self.auto.mkdir()
        self.inputs = {'rebuilt.exe': 'a' * 64}
        manifest = {'format': 2, 'inputs': self.inputs, 'options': [], 'shards': 2,
                    'auto': {'path': str(self.auto), 'files': fingerprint_tree(self.auto)}}
        (self.sweep / 'manifest.json').write_text(json.dumps(manifest))
        summary = {'complete': True, 'shard_exit_codes': [0, 0], 'rows': 2,
                   'verdicts': {'verified': 1, 'timeout': 1}}
        (self.sweep / 'summary.json').write_text(json.dumps(summary))
        (self.sweep / 'av_0.tsv').write_text('004402A0\tverified\t0.75\t30 ok\n')
        (self.sweep / 'av_1.tsv').write_text('0048CC40\ttimeout\t0.00\twall-clock limit\n')

    def load(self, inputs):
        return read_sweep(self.sweep, inputs, self.auto, {0x4402A0, 0x48CC40})

    def test_preserves_raw_verdicts_only_for_the_matching_build(self):
        rows, sweep = self.load(self.inputs)
        self.assertEqual(rows['0048CC40']['verdict'], 'timeout')
        self.assertEqual(rows['004402A0']['normal_coverage'], 0.75)
        self.assertEqual(sweep['rows'], 2)
        with self.assertRaisesRegex(ValueError, 'different build inputs'):
            self.load({'rebuilt.exe': 'b' * 64})

    def test_summary_cannot_hide_an_incomplete_or_duplicate_shard(self):
        shard = self.sweep / 'av_0.tsv'
        row = shard.read_text()
        shard.write_text('')
        with self.assertRaisesRegex(ValueError, 'missing 1 expected addresses'):
            self.load(self.inputs)
        shard.write_text(row * 2)
        with self.assertRaisesRegex(ValueError, 'duplicate address 004402A0'):
            self.load(self.inputs)


if __name__ == '__main__':
    unittest.main()
