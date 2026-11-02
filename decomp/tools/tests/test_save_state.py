"""Negative controls for save-state comparison and the shared GRES fixture boundary."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, TOOLS / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


save = module('save_state')
fixture = module('make_wine_fixture')


def instruction(name, a=0, b=0, c=0):
    return save.lua.OPS.index(name) | a << 6 | c << 14 | b << 23


class SaveStateTests(unittest.TestCase):
    def test_data_constructor_and_changed_value_control(self):
        code = [instruction('NEWTABLE'), instruction('SETTABLE', b=256, c=257),
                instruction('SETGLOBAL', c=2), instruction('RETURN', b=1)]
        original = save.evaluate({'k': ['Gold', 100.0, 'Serialize'], 'code': code})
        wrong = save.evaluate({'k': ['Gold', 101.0, 'Serialize'], 'code': code})
        self.assertEqual(original, {'Gold': 100.0})
        self.assertEqual(save.differences(save.canonical(original), save.canonical(wrong)),
                         [{'path': 'Serialize/s:Gold', 'left': 100.0, 'right': 101.0}])

    def test_reordered_tables_match_but_key_types_and_signed_zero_do_not(self):
        self.assertEqual(save.differences(save.canonical({'A': 1.0, 'B': 2.0}),
                                          save.canonical({'B': 2.0, 'A': 1.0})), [])
        self.assertNotEqual(save.canonical({1: True}), save.canonical({'1': True}))
        self.assertTrue(save.differences(-0.0, 0.0))

    def test_executable_and_unexpected_global_instructions_are_rejected(self):
        for code, constants in [([instruction('CALL')], []),
                                ([instruction('SETGLOBAL')], ['Unexpected']),
                                ([instruction('CLOSURE')], [])]:
            with self.subTest(code=code), self.assertRaises(ValueError):
                save.evaluate({'k': constants, 'code': code})

    def test_other_bytecode_headers_are_rejected(self):
        with self.assertRaises(ValueError):
            save.decode(b'\x1bLua\x51\x00\x01\x04\x08\x04\x04\x00')

    def test_gres_roundtrip_preserves_original_script_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'fixture.pak'
            fixture.write_pak(path, {'guiscenes.lua': b'unchanged game bytecode', 'driver.lua': b'test code'})
            self.assertEqual(fixture.read_entry(path, 'guiscenes.lua'), b'unchanged game bytecode')
            with self.assertRaises(ValueError):
                fixture.write_pak(path, {})
            with self.assertRaises(ValueError):
                fixture.read_entry(path, 'absent.lua')


if __name__ == '__main__':
    unittest.main()
