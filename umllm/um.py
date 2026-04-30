# Copyright (C) 2026 PUC-Rio/PUC-Behring Institute for AI
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import pathlib
import re

import typing_extensions as ty

Symbol: ty.TypeAlias = str
Tape: ty.TypeAlias = str

_logger: ty.Final[logging.Logger] = logging.getLogger(__name__)


class UM:
    """Universal Turing Machine."""

    SYM_Q: ty.Final[str] = 'Q'
    SYM_S: ty.Final[str] = 'S'
    SYM_0: ty.Final[str] = '0'
    SYM_1: ty.Final[str] = '1'
    SYM_B: ty.Final[str] = '_'
    SYM_L: ty.Final[str] = '<'
    SYM_R: ty.Final[str] = '>'
    SYM_X: ty.Final[str] = '.'

    _alphabet: ty.ClassVar[frozenset[Symbol]] = frozenset([
        SYM_Q,                    # state of the simulated machine
        SYM_S,                    # symbol of the simulated machine
        SYM_0,                    # bit 0
        SYM_1,                    # bit 1
        SYM_B,                    # blank
        SYM_L,                    # left movement indicator
        SYM_R,                    # right movement indicator
        SYM_X,                    # ignored
    ])

    _tr: ty.ClassVar[dict[str, Symbol]] = {
        '₀': SYM_0,
        '₁': SYM_1,
        ' ': SYM_X,
        '|': SYM_X,
    }

    @classmethod
    def check_symbol(cls, value: ty.Any) -> Symbol:
        """Coerces value to symbol."""
        if isinstance(value, str):
            value = cls._tr.get(value, value)
            if value in cls._alphabet:
                return value
        raise ValueError(f'bad symbol: {value}')

    @classmethod
    def check_tape(cls, value: ty.Any) -> Tape:
        """Coerces value to tape (sequence of symbols)."""
        if isinstance(value, str):
            return ''.join(map(cls.check_symbol, value)).replace(
                cls.SYM_X, '')
        else:
            raise ValueError(f'bad tape: {value}')

    @classmethod
    def _check_and_pad(cls, value: ty.Any) -> Tape:
        return cls._pad(cls.check_tape(value))

    @classmethod
    def _pad(cls, tape: Tape) -> Tape:
        s = tape.strip(cls.SYM_B)
        if s == '':
            return Tape(cls.SYM_B)
        else:
            return Tape(cls.SYM_B + s + cls.SYM_B)

    @classmethod
    def _unpad(cls, tape: Tape) -> Tape:
        return Tape(tape.strip(cls.SYM_B) or cls.SYM_B)

    machine: Tape
    work: Tape
    state: Tape
    symbol: Tape
    left_symbol: Tape
    movement: Tape
    next_state: Tape
    next_symbol: Tape
    subst1: Tape
    subst2: Tape

    def __init__(
            self,
            machine: Tape,
            work: Tape,
            state: Tape | None = SYM_B,
            symbol: Tape | None = SYM_B,
            left_symbol: Tape | None = SYM_B,
            movement: Tape | None = SYM_B,
            next_state: Tape | None = SYM_B,
            next_symbol: Tape | None = SYM_B,
            subst1: Tape | None = SYM_B,
            subst2: Tape | None = SYM_B
    ) -> None:
        self.machine = self._check_and_pad(machine)
        self.work = self._check_and_pad(work)
        self.state = self._check_and_pad(state)
        self.symbol = self._check_and_pad(symbol)
        self.left_symbol = self._check_and_pad(left_symbol)
        self.movement = self._check_and_pad(movement)
        self.next_state = self._check_and_pad(next_state)
        self.next_symbol = self._check_and_pad(next_symbol)
        self.subst1 = self._check_and_pad(subst1)
        self.subst2 = self._check_and_pad(subst2)
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
        """Converts dictionary to UM."""
        return cls(**value)

    def to_dict(self) -> dict[str, str]:
        """Converts UM to dictionary."""
        return {
            'machine': self.machine,
            'work': self.work,
            'state': self.state,
            'symbol': self.symbol,
            'left_symbol': self.left_symbol,
            'movement': self.movement,
            'next_state': self.next_state,
            'next_symbol': self.next_symbol,
            'subst1': self.subst1,
            'subst2': self.subst2}

    @classmethod
    def load_string(cls, s: str) -> ty.Self:
        """Loads UM from string."""
        machine: str = ''
        work: str = ''
        it = filter(lambda l: not l.startswith('#'),
                    map(str.strip, s.splitlines()))
        while True:
            line = next(it, '')
            if not line:
                break
            machine += line
        for line in it:
            work += line
        return cls(machine, work)

    @classmethod
    def load_file(cls, path: pathlib.Path | str) -> ty.Self:
        with open(pathlib.Path(path), 'rt', encoding='utf-8') as fp:
            return cls.load_string(fp.read())

    @property
    def _re01(self) -> str:
        return '[' + self.SYM_0 + self.SYM_1 + ']'

    @property
    def _re01s(self) -> str:
        return self._re01 + '+'

    @property
    def _reQn(self) -> str:
        return self.SYM_Q + self._re01s

    @property
    def _reSn(self) -> str:
        return '(?:' + self.SYM_S + self._re01s + '|' + self.SYM_B + ')'

    @property
    def _reLR(self) -> str:
        return '[' + self.SYM_L + self.SYM_R + ']'

    def step1(self) -> None:
        """Step 1: Load `state` and `symbol`."""
        m = re.search(f'({self._reQn})({self._reSn})', self.work)
        if m is None:
            raise RuntimeError(f'bad work: {self.work}')
        self.state = self._check_and_pad(m.group(1))
        self.symbol = self._check_and_pad(m.group(2))
        _logger.info('[step 1] state: %s', self.state)
        _logger.info('[step 1] symbol: %s', self.symbol)

    def step2(self) -> None:
        """Step 2: Load `next_state`, `next_symbol` and `movement`."""
        Qs = self._unpad(self.state)
        Sw = self._unpad(self.symbol)
        m = re.search(
            rf'{Qs}{Sw}({self._reQn})({self._reSn})({self._reLR})',
            self.machine)
        if m is None:
            raise RuntimeError(f'bad machine: {self.machine}')
        Qy, Sz, m = m.groups()  # type: ignore
        _logger.info('[step 2] %s%s ↦ %s%s%s', Qs, Sw, Qy, Sz, m)
        self.next_state = self._check_and_pad(Qy)
        self.next_symbol = self._check_and_pad(Sz)
        self.movement = self._check_and_pad(m)
        _logger.info('[step 2] next state: %s', self.next_state)
        _logger.info('[step 2] next symbol: %s', self.next_symbol)
        _logger.info('[step 2] movement: %s', self.movement)

    def step3(self) -> None:
        """Step 3: Load `left_symbol`."""
        m = re.search(rf'({self._reSn}){self._reQn}', self.work)
        self.left_symbol = self._check_and_pad(
            m.group(1) if m is not None else self.SYM_B)
        _logger.info('[step 3] left symbol: %s', self.left_symbol)

    def step4(self) -> None:
        """Step 4: Load `subst1`."""
        Qs = self._unpad(self.state)
        Sw = self._unpad(self.symbol)
        Su = self._unpad(self.left_symbol)
        mov = self._unpad(self.movement)
        if mov == self.SYM_L:
            self.subst1 = self._check_and_pad(Su + Qs + Sw)
        elif mov == self.SYM_R:
            self.subst1 = self._check_and_pad(Qs + Sw)
        else:
            raise RuntimeError('should not get here')
        _logger.info('[step 4] subst1: %s', self.subst1)

    def step5(self) -> None:
        """Step 5: Load `subst2`"""
        Qy = self._unpad(self.next_state)
        Sz = self._unpad(self.next_symbol)
        Su = self._unpad(self.left_symbol)
        mov = self._unpad(self.movement)
        if mov == self.SYM_L:
            self.subst2 = self._check_and_pad(Qy + Su + Sz)
        elif mov == self.SYM_R:
            self.subst2 = self._check_and_pad(Sz + Qy)
        else:
            raise RuntimeError('should not get here')
        _logger.info('[step 5] subst2: %s', self.subst2)

    def step6(self) -> None:
        """Step 6: Replace `subst1` by `subst2` in `work`."""
        s1 = self._unpad(self.subst1)
        s2 = self._unpad(self.subst2)
        self.work = self._check_and_pad(
            self._unpad(self.work).replace(s1, s2, 1))
        _logger.info('[step 6] work: %s', self.work)

    class Run:
        """The current run."""

        #: Parent UM.
        um: UM

        #: Current step.
        step: int

        #: Total steps.
        total: int

        def __init__(self, um: UM) -> None:
            self.um = um
            self.step = 0
            self.total = 0

        def __str__(self) -> str:
            def it() -> ty.Iterator[str]:
                yield (f'#{self.total} (after step{self.step})')
                yield str(self.um)
                yield ''
            return '\n'.join(it())

        def __next__(self) -> ty.Self:
            self.step = (self.step % 6) + 1
            getattr(self.um, f'step{self.step}')()
            self.total += 1
            return self

    def run(self) -> Run:
        """Runs the UM."""
        return self.Run(self)
