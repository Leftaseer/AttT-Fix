"""x87-to-binary64 decoding must handle the wider finite exponent range."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from difftest import Harness
from unicorn.x86_const import UC_X86_REG_FPSW


def decode(mantissa, exponent):
    class Registers:
        def reg_read(self, register):
            return 0 if register == UC_X86_REG_FPSW else (mantissa, exponent)

    h = Harness.__new__(Harness)
    h.uc = Registers()
    return h._st0()


class X87DecodeTests(unittest.TestCase):
    def test_finite_values_beyond_binary64_range(self):
        # x87 can represent 2**1024 and much larger finite numbers; converting
        # those to binary64 produces infinity, rather than a Python exception.
        for exponent in (16383 + 1024, 16383 + 16000, 0x7ffe):
            for sign in (0, 0x8000):
                with self.subTest(exponent=exponent, sign=sign):
                    self.assertEqual(decode(1 << 63, exponent | sign),
                                     -math.inf if sign else math.inf)

    def test_largest_binary64_and_rounding_overflow(self):
        self.assertEqual(decode(0xfffffffffffff800, 16383 + 1023), sys.float_info.max)
        # Rounding the 64-bit significand up can also overflow at this exponent.
        self.assertEqual(decode(0xffffffffffffffff, 16383 + 1023), math.inf)

    def test_ordinary_values_and_signed_zero(self):
        self.assertEqual(decode(1 << 63, 16383), 1.0)
        self.assertEqual(decode(1 << 63, (16383 + 1) | 0x8000), -2.0)
        for sign in (0, 0x8000):
            result = decode(0, sign)
            self.assertEqual(result, 0.0)
            self.assertEqual(math.copysign(1.0, result), -1.0 if sign else 1.0)

    def test_special_values(self):
        self.assertEqual(decode(1 << 63, 0x7fff), math.inf)
        self.assertEqual(decode(1 << 63, 0xffff), -math.inf)
        self.assertTrue(math.isnan(decode(0xc000000000000000, 0x7fff)))


if __name__ == '__main__':
    unittest.main()
