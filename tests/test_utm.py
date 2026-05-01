# Copyright (C) 2026 PUC-Rio/PUC-Behring Institute for AI
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from umllm import UM


class Test(unittest.TestCase):

    def test_check_symbol(self) -> None:
        self.assertEqual(UM.check_symbol('Q'), UM.SYM_Q)
        self.assertEqual(UM.check_symbol('S'), UM.SYM_S)
        self.assertEqual(UM.check_symbol('0'), UM.SYM_0)
        self.assertEqual(UM.check_symbol('₀'), UM.SYM_0)
        self.assertEqual(UM.check_symbol('₁'), UM.SYM_1)
        self.assertEqual(UM.check_symbol('_'), UM.SYM_B)
        self.assertEqual(UM.check_symbol('<'), UM.SYM_L)
        self.assertEqual(UM.check_symbol('>'), UM.SYM_R)
        self.assertEqual(UM.check_symbol('.'), UM.SYM_X)
        self.assertRaises(ValueError, UM.check_symbol, '#')
        self.assertRaises(ValueError, UM.check_symbol, 0)

    def test_check_tape(self) -> None:
        self.assertEqual(UM.check_tape(''), '')
        self.assertEqual(UM.check_tape('Q₀₁'), 'Q01')
        self.assertEqual(UM.check_tape('Q₀.₁'), 'Q01')
        self.assertEqual(UM.check_tape('|Q₀.₁|'), 'Q01')
        self.assertEqual(
            UM.check_tape(
                'Q0S0Q0S0> Q0S1Q0S1>  Q0_Q₁_<.Q1S0Q10S1> Q1S1Q1S0<.Q1_Q10S1>'),
            'Q0S0Q0S0>Q0S1Q0S1>Q0_Q1_<Q1S0Q10S1>Q1S1Q1S0<Q1_Q10S1>')

    def test__init__(self) -> None:
        um = UM('Q0S0Q0S0>', 'Q0', 'Q0S0')
        self.assertEqual(um.machine, '_Q0S0Q0S0>_')
        self.assertEqual(um.halt, '_Q0_')
        self.assertEqual(um.work, '_Q0S0_')
        self.assertEqual(um.state, '_')
        self.assertEqual(um.symbol, '_')
        self.assertEqual(um.left_symbol, '_')
        self.assertEqual(um.movement, '_')
        self.assertEqual(um.next_state, '_')
        self.assertEqual(um.next_symbol, '_')
        self.assertEqual(um.subst1, '_')
        self.assertEqual(um.subst2, '_')
        self.assertEqual(um.steps, 0)
        self.assertEqual(um.stepno, 0)
        self.assertEqual(um.cycles, 0)


if __name__ == '__main__':
    unittest.main()
