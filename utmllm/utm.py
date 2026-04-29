# Copyright (C) 2026 PUC-Rio/PUC-Behring Institute for AI
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import re

import typing_extensions as ty

Symbol = ty.NewType('Symbol', str)
TSymbol: ty.TypeAlias = Symbol | str

Tape = ty.NewType('Tape', str)
TTape: ty.TypeAlias = Tape | str

_logger: Final[logging.Logger] = logging.getLogger(__name__)


class UTM:
    """Universal Turing Machine."""

    #: State of the simulated machine (indicator).
    Q: ty.ClassVar[Symbol] = Symbol('Q')

    #: Symbol of the simulated machine (indicator).
    S: ty.ClassVar[Symbol] = Symbol('S')

    #: The binary digit "0".
    Zero: ty.ClassVar[Symbol] = Symbol('0')

    #: The binary digit "1".
    One: ty.ClassVar[Symbol] = Symbol('1')

    #: The blank symbol.
    Blank: ty.ClassVar[Symbol] = Symbol('_')

    #: Left-movement indicator.
    Left: ty.ClassVar[Symbol] = Symbol('<')

    #: Right-movement indicator.
    Right: ty.ClassVar[Symbol] = Symbol('>')

    #: Comment (pseudo-symbol, deleted from input).
    Comment: ty.ClassVar[Symbol] = Symbol('.')

    _valid_symbols: ty.ClassVar[frozenset[Symbol]] = frozenset([
        Q, S, Zero, One, Blank, Left, Right, Comment])

    @classmethod
    def check_symbol(cls, value: ty.Any) -> Symbol:
        """Coerces value to symbol."""
        if isinstance(value, str) and value in cls._valid_symbols:
            return Symbol(value)
        else:
            raise ValueError(f'bad symbol: {value}')

    @classmethod
    def check_tape(cls, value: ty.Any) -> Tape:
        """Coerces value to tape."""
        if isinstance(value, str):
            return Tape(''.join(map(
                cls.check_symbol, value)).replace(cls.Comment, ''))
        else:
            raise ValueError(f'bad tape: {value}')

    @classmethod
    def _check_and_pad(cls, value: ty.Any) -> Tape:
        return cls._pad(cls.check_tape(value))

    @classmethod
    def _pad(cls, tape: Tape) -> Tape:
        s = tape.strip(cls.Blank)
        return Tape(s) if s == '' else Tape(cls.Blank + s + cls.Blank)

    @classmethod
    def _unpad(cls, tape: Tape) -> Tape:
        return Tape(tape.strip(cls.Blank) or cls.Blank)

    machine: Tape
    work: Tape
    current_state: Tape
    current_symbol: Tape
    left_symbol: Tape
    movement: Tape
    next_state: Tape
    next_symbol: Tape
    subst1: Tape
    subst2: Tape

    def __init__(
            self,
            machine: TTape,
            work: TTape,
            current_state: TTape | None = None,
            current_symbol: TTape | None = None,
            left_symbol: TTape | None = None,
            movement: TTape | None = None,
            next_state: TTape | None = None,
            next_symbol: TTape | None = None,
            subst1: TTape | None = None,
            subst2: TTape | None = None
    ) -> None:
        self.machine = self._check_and_pad(machine)
        self.work = self._check_and_pad(work)
        self.current_state = self._check_and_pad(current_state or '')
        self.current_symbol = self._check_and_pad(current_symbol or '')
        self.left_symbol = self._check_and_pad(left_symbol or '')
        self.movement = self._check_and_pad(movement or '')
        self.next_state = self._check_and_pad(next_state or '')
        self.next_symbol = self._check_and_pad(next_symbol or '')
        self.subst1 = self._check_and_pad(subst1 or '')
        self.subst2 = self._check_and_pad(subst2 or '')
        _logger.info('[init] machine: %s', self.machine)
        _logger.info('[init] work: %s', self.work)

    def __str__(self) -> str:
        t = self.to_dict()
        tab = max(*map(len, t.keys()))

        def it() -> ty.Iterator[str]:
            for k, v in t.items():
                yield f'{k:>{tab}}: {v}'
        return '\n'.join(it())

    @classmethod
    def of_dict(cls, value: dict[str, str]) -> ty.Self:
        """Converts dictionary to UTM."""
        return cls(**value)

    def to_dict(self) -> dict[str, str]:
        """Converts UTM to dictionary."""
        return {
            'machine': self.machine,
            'work': self.work,
            'current_state': self.current_state,
            'current_symbol': self.current_symbol,
            'left_symbol': self.left_symbol,
            'movement': self.movement,
            'next_state': self.next_state,
            'next_symbol': self.next_symbol,
            'subst1': self.subst1,
            'subst2': self.subst2}

    _re_01: ty.ClassVar[str] =\
        '[' + Zero + One + ']'

    _re_01s: ty.ClassVar[str] =\
        _re_01 + '+'

    _re_Qx: ty.ClassVar[str] =\
        Q + _re_01s

    _re_Sx_or_blank: ty.ClassVar[str] =\
        '(?:' + S + _re_01s + '|' + Blank + ')'

    _re_LR: ty.ClassVar[str] =\
        '[' + Left + Right + ']'

    def step1(self) -> None:
        """Step 1: Load current state."""
        m = re.search(
            rf'({self._re_Qx})[{self.S}{self.Blank}]',
            str(self.work))
        if m is None:
            raise RuntimeError(f'bad work: {self.work}')
        self.current_state = self._check_and_pad(m.group(1))
        _logger.info('[step 1] current state: %s', self.current_state)

    def step2(self) -> None:
        """Step 2: Load current symbol."""
        assert self.current_state
        Qs = self._unpad(self.current_state)
        m = re.search(rf'{Qs}({self._re_Sx_or_blank})', str(self.work))
        if m is None:
            raise RuntimeError(f'bad work: {self.work}')
        self.current_symbol = self._check_and_pad(m.group(1))
        _logger.info('[step 2] current symbol: %s', self.current_symbol)

    def step3(self) -> None:
        """Step 3: Load next state, next symbol and movement."""
        assert self.current_state
        Qs = self._unpad(self.current_state)
        Sw = self._unpad(self.current_symbol)
        m = re.search(
            rf'{Qs}{Sw}({self._re_Qx})({self._re_Sx_or_blank})({self._re_LR})',
            str(self.machine))
        if m is None:
            raise RuntimeError(f'bad machine: {self.machine}')
        Qy, Sz, m = m.groups()  # type: ignore
        _logger.info('[step 3] %s%s ↦ %s%s%s', Qs, Sw, Qy, Sz, m)
        self.next_state = self._check_and_pad(Qy)
        self.next_symbol = self._check_and_pad(Sz)
        self.movement = self._check_and_pad(m)
        _logger.info('[step 3] next state: %s', self.next_state)
        _logger.info('[step 3] next symbol: %s', self.next_symbol)
        _logger.info('[step 3] movement: %s', self.movement)

    def step4(self) -> None:
        """Step4: Load left symbol."""
        assert self.work
        m = re.search(
            rf'({self._re_Sx_or_blank}){self._re_Qx}',
            str(self.work))
        self.left_symbol = self._check_and_pad(
            m.group(1) if m is not None else self.Blank)
        _logger.info('[step 4] left symbol: %s', self.left_symbol)

    def step5(self) -> None:
        """Step 5: Load subst1."""
        assert self.current_state
        assert self.movement
        Qs = self._unpad(self.current_state)
        Sw = self._unpad(self.current_symbol)
        Su = self._unpad(self.left_symbol)
        m = self._unpad(self.movement)
        assert m == self.Left or m == self.Right
        if m == self.Left:
            self.subst1 = self._check_and_pad(Su + Qs + Sw)
        elif m == self.Right:
            self.subst1 = self._check_and_pad(Qs + Sw)
        else:
            raise RuntimeError('should not get here')
        _logger.info('[step 5] subst1: %s', self.subst1)

    def step6(self) -> None:
        """Step 6: Load subst2"""
        assert self.next_state
        assert self.movement
        Qy = self._unpad(self.next_state)
        Sz = self._unpad(self.next_symbol)
        Su = self._unpad(self.left_symbol)
        m = self._unpad(self.movement)
        if m == self.Left:
            self.subst2 = self._check_and_pad(Qy + Su + Sz)
        elif m == self.Right:
            self.subst2 = self._check_and_pad(Sz + Qy)
        else:
            raise RuntimeError('should not get here')
        _logger.info('[step 6] subst2: %s', self.subst2)

    def step7(self) -> None:
        """Step 7: Replace subst1 by subst2 in work."""
        assert self.subst1
        assert self.subst2
        s1 = self._unpad(self.subst1)
        s2 = self._unpad(self.subst2)
        self.work = self._check_and_pad(
            self._unpad(self.work).replace(s1, s2, 1))
        _logger.info('[step 7] work: %s', self.work)
