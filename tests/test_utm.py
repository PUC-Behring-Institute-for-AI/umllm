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
        self.assertEqual(UM.check_symbol('L'), UM.SYM_L)
        self.assertEqual(UM.check_symbol('R'), UM.SYM_R)
        self.assertEqual(UM.check_symbol(' '), UM.SYM_X)
        self.assertRaises(ValueError, UM.check_symbol, '#')
        self.assertRaises(ValueError, UM.check_symbol, 0)

    def test_check_tape(self) -> None:
        self.assertEqual(UM.check_tape(''), '')
        self.assertEqual(UM.check_tape('Q₀₁'), 'Q01')
        self.assertEqual(UM.check_tape('Q₀|₁'), 'Q01')
        self.assertEqual(UM.check_tape('|Q₀ ₁|'), 'Q01')
        self.assertEqual(
            UM.check_tape(
                'Q0S0Q0S0R Q0S1Q0S1R  Q0_Q₁_L|Q1S0Q10S1R Q1S1Q1S0L|Q1_Q10S1R'),
            'Q0S0Q0S0RQ0S1Q0S1RQ0.Q1.LQ1S0Q10S1RQ1S1Q1S0LQ1.Q10S1R')

    def test__init__(self) -> None:
        um = UM('Q0S0Q0S0R', 'Q0', 'Q0S0')
        self.assertEqual(um.machine, 'Q0S0Q0S0R')
        self.assertEqual(um.halt, 'Q0')
        self.assertEqual(um.work, '.Q0S0.')
        self.assertEqual(um.state, '')
        self.assertEqual(um.symbol, '')
        self.assertEqual(um.left_symbol, '')
        self.assertEqual(um.next_state, '')
        self.assertEqual(um.next_symbol, '')
        self.assertEqual(um.next_move, '')
        self.assertEqual(um.subst1, '')
        self.assertEqual(um.subst2, '')
        self.assertEqual(um.steps, 0)
        self.assertIsNone(um.prev_step)
        self.assertIsNone(um.next_step)
        self.assertEqual(um.cycles, 0)


if __name__ == '__main__':
    unittest.main()
