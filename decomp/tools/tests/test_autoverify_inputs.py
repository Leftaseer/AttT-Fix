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
from verify_sweep import interruption_record


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


if __name__ == '__main__':
    unittest.main()
