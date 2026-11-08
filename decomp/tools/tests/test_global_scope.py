import unittest

import autodecomp


class GlobalScopeTests(unittest.TestCase):
    """A newer symbol table prints data as 'Class::G_XXXXXXXX'; the scope is not part of the address."""

    ADDR = '00401000'

    def setUp(self):
        self._machine = dict(autodecomp.machine)
        self._convs = dict(autodecomp.convs)
        autodecomp.machine[int(self.ADDR, 16)] = (set(), 0)
        autodecomp.convs.pop(int(self.ADDR, 16), None)

    def tearDown(self):
        autodecomp.machine.clear()
        autodecomp.machine.update(self._machine)
        autodecomp.convs.clear()
        autodecomp.convs.update(self._convs)

    def convert(self, statement):
        f = {
            'a': self.ADDR,
            'code': '\nundefined4 __cdecl f_%s(void)\n\n{\n  %s;\n}\n' % (self.ADDR, statement),
            'callees': [],
            'globals': {'006C884C': 'undefined4'},
            'strings': [],
        }
        protos = {int(self.ADDR, 16): ['__cdecl', False, 'undefined4', [], False, []]}
        return autodecomp.convert(f, protos, set(), set(), {})

    def test_class_scoped_global_is_the_address(self):
        out, why = self.convert('return CConfig::G_006C884C')
        self.assertIsNone(why)
        self.assertIn('G_006C884C', out[2])

    def test_other_cpp_names_are_still_rejected(self):
        out, why = self.convert('return CConfig::G_Something')
        self.assertIsNone(out)
        self.assertEqual(why, 'C++ name left')


if __name__ == '__main__':
    unittest.main()
