# Copyright (C) 2026 PUC-Rio/PUC-Behring Institute for AI
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from utmllm import UTM


class Test(unittest.TestCase):

    def test_check_symbol(self) -> None:
        self.assertEqual(UTM.check_symbol('Q'), UTM.SYM_Q)
        self.assertEqual(UTM.check_symbol('S'), UTM.SYM_S)
        self.assertEqual(UTM.check_symbol('0'), UTM.SYM_0)
        self.assertEqual(UTM.check_symbol('₀'), UTM.SYM_0)
        self.assertEqual(UTM.check_symbol('₁'), UTM.SYM_1)
        self.assertEqual(UTM.check_symbol('_'), UTM.SYM_B)
        self.assertEqual(UTM.check_symbol('<'), UTM.SYM_L)
        self.assertEqual(UTM.check_symbol('>'), UTM.SYM_R)
        self.assertEqual(UTM.check_symbol('.'), UTM.SYM_X)
        self.assertRaises(ValueError, UTM.check_symbol, '#')
        self.assertRaises(ValueError, UTM.check_symbol, 0)

    def test_check_tape(self) -> None:
        self.assertEqual(UTM.check_tape(''), '')
        self.assertEqual(UTM.check_tape('Q₀₁'), 'Q01')
        self.assertEqual(UTM.check_tape('Q₀.₁'), 'Q01')
        self.assertEqual(UTM.check_tape('|Q₀.₁|'), 'Q01')
        self.assertEqual(
            UTM.check_tape(
                'Q0S0Q0S0> Q0S1Q0S1>  Q0_Q₁_<.Q1S0Q10S1> Q1S1Q1S0<.Q1_Q10S1>'),
            'Q0S0Q0S0>Q0S1Q0S1>Q0_Q1_<Q1S0Q10S1>Q1S1Q1S0<Q1_Q10S1>')

    def test__init__(self) -> None:
        utm = UTM('Q0S0Q0S0>', 'Q0S0')
        self.assertEqual(utm.machine, '_Q0S0Q0S0>_')
        self.assertEqual(utm.work, '_Q0S0_')
        self.assertEqual(utm.state, '_')
        self.assertEqual(utm.symbol, '_')
        self.assertEqual(utm.left_symbol, '_')
        self.assertEqual(utm.movement, '_')
        self.assertEqual(utm.next_state, '_')
        self.assertEqual(utm.next_symbol, '_')
        self.assertEqual(utm.subst1, '_')
        self.assertEqual(utm.subst2, '_')


if __name__ == '__main__':
    unittest.main()
