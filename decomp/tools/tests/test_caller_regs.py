import unittest

import autodecomp


class CallerRegsExemptionTests(unittest.TestCase):
    """symbols/GAME_callerregs.tsv: a callee that records the caller's context reads registers that are not
    arguments, so its prototype may lack them (0047C4F0, called cdecl(frames, report))."""

    ADDR = 0x47C4F0

    def setUp(self):
        self._machine = dict(autodecomp.machine)
        self._caller_regs = dict(autodecomp.caller_regs)
        self._convs = dict(autodecomp.convs)
        self._stack_slots = dict(autodecomp.stack_slots)
        autodecomp.machine[self.ADDR] = ({'EAX', 'EBX', 'ECX', 'EDI', 'EDX', 'ESI'}, 0)
        autodecomp.stack_slots.pop(self.ADDR, None)
        autodecomp.convs.pop(self.ADDR, None)

    def tearDown(self):
        autodecomp.machine.clear()
        autodecomp.machine.update(self._machine)
        autodecomp.caller_regs.clear()
        autodecomp.caller_regs.update(self._caller_regs)
        autodecomp.convs.clear()
        autodecomp.convs.update(self._convs)
        autodecomp.stack_slots.clear()
        autodecomp.stack_slots.update(self._stack_slots)

    def proto(self):
        return ['__cdecl', False, 'undefined4', [('int', 'frames'), ('char *', 'report')], False,
                ['stack', 'stack']]

    def test_registers_the_prototype_lacks_are_rejected(self):
        why = autodecomp.fit_convention(self.ADDR, self.proto())
        self.assertEqual(why, 'reads registers the prototype lacks (EAX,EBX,ECX,EDI,EDX,ESI)')

    def test_listed_callee_is_fitted_as_cdecl(self):
        autodecomp.caller_regs[self.ADDR] = 'context capture'
        self.assertIsNone(autodecomp.fit_convention(self.ADDR, self.proto()))
        self.assertEqual(autodecomp.convs[self.ADDR], ([], 0))

    def test_exemption_does_not_hide_a_stack_mismatch(self):
        autodecomp.caller_regs[self.ADDR] = 'context capture'
        autodecomp.stack_slots[self.ADDR] = 3
        why = autodecomp.fit_convention(self.ADDR, self.proto())
        self.assertEqual(why, 'stack parameters the decompiler missed')


if __name__ == '__main__':
    unittest.main()
