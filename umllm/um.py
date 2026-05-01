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
    """Universal Machine."""

    #: State of the simulated machine.
    SYM_Q: ty.Final[str] = 'Q'

    #: Symbol of the simulated machine.
    SYM_S: ty.Final[str] = 'S'

    #: The binary digit "0".
    SYM_0: ty.Final[str] = '0'

    #: The binary digit "1".
    SYM_1: ty.Final[str] = '1'

    #: The blank symbol.
    SYM_B: ty.Final[str] = '_'

    #: Left-movement indicator.
    SYM_L: ty.Final[str] = '<'

    #: Right-movement indicator.
    SYM_R: ty.Final[str] = '>'

    #: Ignored.
    SYM_X: ty.Final[str] = '.'

    _alphabet: ty.ClassVar[frozenset[Symbol]] =\
        frozenset([SYM_Q, SYM_S, SYM_0, SYM_1, SYM_B, SYM_L, SYM_R, SYM_X,])

    _tr: ty.ClassVar[dict[str, Symbol]] = {
        'q': SYM_Q,
        's': SYM_S,
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
        """Coerces value to tape."""
        if isinstance(value, str):
            return ''.join(map(cls.check_symbol, value)).replace(cls.SYM_X, '')
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

    class Error(Exception):
        """UM error."""

    #: Transition table of the simulated machine.
    _machine: Tape

    #: Halting state of the simulated machine.
    _halt: Tape

    #: Work tape of the simulated machine.
    _work: Tape

    #: Current state of the simulated machine.
    _state: Tape

    #: Current symbol of the simulated machine (being read by head).
    _symbol: Tape

    #: Symbol to the left of the head.
    _left_symbol: Tape

    #: The direction to move the head next.
    _movement: Tape

    #: The state to transition to before moving the head.
    _next_state: Tape

    #: The symbol to write before moving the head.
    _next_symbol: Tape

    #: Substitution source (what to match in work).
    _subst1: Tape

    #: Substitution target (what to replace `subst1` by in work).
    _subst2: Tape

    #: Total number of steps executed.
    _steps: int

    def __init__(
            self,
            machine: Tape,
            halt: Tape,
            work: Tape,
            state: Tape | None = None,
            symbol: Tape | None = None,
            left_symbol: Tape | None = None,
            movement: Tape | None = None,
            next_state: Tape | None = None,
            next_symbol: Tape | None = None,
            subst1: Tape | None = None,
            subst2: Tape | None = None,
            steps: int | None = None,
    ) -> None:
        self._machine = self._check_and_pad(machine)
        self._halt = self._check_and_pad(halt)
        self._work = self._check_and_pad(work)
        self._state = self._check_and_pad(state or self.SYM_B)
        self._symbol = self._check_and_pad(symbol or self.SYM_B)
        self._left_symbol = self._check_and_pad(left_symbol or self.SYM_B)
        self._movement = self._check_and_pad(movement or self.SYM_B)
        self._next_state = self._check_and_pad(next_state or self.SYM_B)
        self._next_symbol = self._check_and_pad(next_symbol or self.SYM_B)
        self._subst1 = self._check_and_pad(subst1 or self.SYM_B)
        self._subst2 = self._check_and_pad(subst2 or self.SYM_B)
        self._steps = abs(steps or 0)
        _logger.info('[init] machine: %s', self.machine)
        _logger.info('[init] halt: %s', self.halt)
        _logger.info('[init] work: %s', self.work)

    def __str__(self) -> str:
        t = self.to_dict()
        tab = max(*map(len, t.keys()))

        def it() -> ty.Iterator[str]:
            for k, v in t.items():
                yield f'{k:>{tab}}: {v}'
                if k == 'machine':
                    pfx = f'{"":>{tab}}'
                    yield ''
                    for i, (q0, s0, q1, s1, d) in enumerate(  # type: ignore
                            self._parse_machine(), 1):
                        yield pfx + (f'{i:>{3}}: '
                                     f'({q0}, {s0}) ↦ ({q1}, {s1}, {d})')
                    yield ''
        return '\n'.join(it())

    @property
    def machine(self) -> Tape:
        return self._machine

    @machine.setter
    def machine(self, s: Tape) -> None:
        self._machine = self._check_and_pad(s)

    @property
    def halt(self) -> Tape:
        return self._halt

    @halt.setter
    def halt(self, s: Tape) -> None:
        self._halt = self._check_and_pad(s)

    @property
    def work(self) -> Tape:
        return self._work

    @work.setter
    def work(self, s: Tape) -> None:
        self._work = self._check_and_pad(s)

    @property
    def state(self) -> Tape:
        return self._state

    @state.setter
    def state(self, s: Tape) -> None:
        self._state = self._check_and_pad(s)

    @property
    def symbol(self) -> Tape:
        return self._symbol

    @symbol.setter
    def symbol(self, s: Tape) -> None:
        self._symbol = self._check_and_pad(s)

    @property
    def left_symbol(self) -> Tape:
        return self._left_symbol

    @left_symbol.setter
    def left_symbol(self, s: Tape) -> None:
        self._left_symbol = self._check_and_pad(s)

    @property
    def movement(self) -> Tape:
        return self._movement

    @movement.setter
    def movement(self, s: Tape) -> None:
        self._movement = self._check_and_pad(s)

    @property
    def next_state(self) -> Tape:
        return self._next_state

    @next_state.setter
    def next_state(self, s: Tape) -> None:
        self._next_state = self._check_and_pad(s)

    @property
    def next_symbol(self) -> Tape:
        return self._next_symbol

    @next_symbol.setter
    def next_symbol(self, s: Tape) -> None:
        self._next_symbol = self._check_and_pad(s)

    @property
    def subst1(self) -> Tape:
        return self._subst1

    @subst1.setter
    def subst1(self, s: Tape) -> None:
        self._subst1 = self._check_and_pad(s)

    @property
    def subst2(self) -> Tape:
        return self._subst2

    @subst2.setter
    def subst2(self, s: Tape) -> None:
        self._subst2 = self._check_and_pad(s)

    @property
    def steps(self) -> int:
        """Total number of steps executed."""
        return self._steps

    @property
    def stepno(self) -> int:
        """Next step to be executed (0-5)."""
        return self.steps % 6

    @property
    def cycles(self) -> int:
        """Total number of cycles executed."""
        return self.steps // 6

    @classmethod
    def of_dict(cls, value: dict[str, ty.Any]) -> ty.Self:
        """Converts dictionary to UM."""
        return cls(**value)

    def to_dict(self) -> dict[str, ty.Any]:
        """Converts UM to dictionary."""
        return {
            'machine': self.machine,
            'halt': self.halt,
            'work': self.work,
            'state': self.state,
            'symbol': self.symbol,
            'left_symbol': self.left_symbol,
            'movement': self.movement,
            'next_state': self.next_state,
            'next_symbol': self.next_symbol,
            'subst1': self.subst1,
            'subst2': self.subst2,
            'steps': self.steps}

    @classmethod
    def load(cls, s: str) -> ty.Self:
        """Loads UM from string."""
        machine: str = ''
        halt: str = ''
        work: str = ''
        it = filter(lambda l: not l.startswith('#'),
                    map(str.strip, s.splitlines()))
        while True:
            line = next(it, '')
            if not line:
                break
            machine += line
        while True:
            line = next(it, '')
            if not line:
                break
            halt += line
        for line in it:
            work += line
        return cls(machine, halt, work)

    @classmethod
    def load_file(cls, path: pathlib.Path | str) -> ty.Self:
        with open(pathlib.Path(path), 'rt', encoding='utf-8') as fp:
            return cls.load(fp.read())

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

    def _parse_machine(self) -> ty.Sequence[str]:
        m = re.findall(
            f'({self._reQn})'
            + f'({self._reSn})'
            + f'({self._reQn})'
            + f'({self._reSn})'
            + f'({self._reLR})',
            self.machine)
        return m

    def _parse_halt(self) -> str:
        m = re.match(f'({self._reSn})', self.halt)
        if m is None:
            raise self.Error(f'bad halt: {self.halt}')
        return m.group(1)

    def _parse_work(self) -> tuple[str, str, str]:
        m = re.match(
            f'({self._reSn})'
            + f'({self._reQn})'
            + f'({self._reSn})',
            self.work)
        if m is None:
            raise self.Error(f'bad work: {self.work}')
        return m.groups()       # type: ignore

    def run(self) -> ty.Self:
        """Executes cycles until the halting state is reached."""
        _logger.info('[run]')
        while not self.halted():
            self.cycle()
        return self

    def cycle(self) -> ty.Self:
        """Executes one cycle."""
        _logger.info('[cycle %d]', self.cycles)
        while not self.halted():
            self.step()
            if self.stepno == 0:
                break
        return self

    def step(self) -> ty.Self:
        """Executes one step."""
        m = re.search(f'({self._reQn})', self.work)
        if m is None:
            raise self.Error(f'bad work: {self.work}')
        if self.halted():
            return self
        else:
            return getattr(self, f'step{self.stepno}')()

    def halted(self) -> bool:
        """Tests whether UM has halted."""
        m = re.search(f'({self._reQn})', self.work)
        if m is None:
            raise self.Error(f'bad work: {self.work}')
        return self._unpad(self.halt) == m.group(1)

    def step0(self) -> ty.Self:
        """Load `state` and `symbol`."""
        m = re.search(f'({self._reQn})({self._reSn})', self.work)
        if m is None:
            raise self.Error(f'bad work: {self.work}')
        self.state = self._check_and_pad(m.group(1))
        self.symbol = self._check_and_pad(m.group(2))
        _logger.info('[step %d] state: %s', self.stepno, self.state)
        _logger.info('[step %d] symbol: %s', self.stepno, self.symbol)
        self._steps += 1
        return self

    def step1(self) -> ty.Self:
        """Load `next_state`, `next_symbol`, and `movement`."""
        Qs = self._unpad(self.state)
        Sw = self._unpad(self.symbol)
        m = re.search(
            rf'{Qs}{Sw}({self._reQn})({self._reSn})({self._reLR})',
            self.machine)
        if m is None:
            raise self.Error(f'bad machine: {self.machine}')
        Qy, Sz, m = m.groups()  # type: ignore
        _logger.info(
            '[step %d] (%s, %s) ↦ (%s, %s, %s)',
            self.stepno, Qs, Sw, Qy, Sz, m)
        self.next_state = self._check_and_pad(Qy)
        self.next_symbol = self._check_and_pad(Sz)
        self.movement = self._check_and_pad(m)
        _logger.info(
            '[step %d] next state: %s', self.stepno, self.next_state)
        _logger.info(
            '[step %d] next symbol: %s', self.stepno, self.next_symbol)
        _logger.info(
            '[step %d] movement: %s', self.stepno, self.movement)
        self._steps += 1
        return self

    def step2(self) -> ty.Self:
        """Load `left_symbol`."""
        m = re.search(rf'({self._reSn}){self._reQn}', self.work)
        self.left_symbol = self._check_and_pad(
            m.group(1) if m is not None else self.SYM_B)
        _logger.info(
            '[step %d] left symbol: %s', self.stepno, self.left_symbol)
        self._steps += 1
        return self

    def step3(self) -> ty.Self:
        """Load `subst1`."""
        Qs = self._unpad(self.state)
        Sw = self._unpad(self.symbol)
        Su = self._unpad(self.left_symbol)
        mov = self._unpad(self.movement)
        if mov == self.SYM_L:
            self.subst1 = self._check_and_pad(Su + Qs + Sw)
        elif mov == self.SYM_R:
            self.subst1 = self._check_and_pad(Qs + Sw)
        else:
            raise self.Error(f'bad movement: {mov}')
        _logger.info('[step %d] subst1: %s', self.stepno, self.subst1)
        self._steps += 1
        return self

    def step4(self) -> ty.Self:
        """Load `subst2`"""
        Qy = self._unpad(self.next_state)
        Sz = self._unpad(self.next_symbol)
        Su = self._unpad(self.left_symbol)
        mov = self._unpad(self.movement)
        if mov == self.SYM_L:
            self.subst2 = self._check_and_pad(Qy + Su + Sz)
        elif mov == self.SYM_R:
            self.subst2 = self._check_and_pad(Sz + Qy)
        else:
            raise self.Error(f'bad movement: {mov}')
        _logger.info('[step %d] subst2: %s', self.stepno, self.subst2)
        self._steps += 1
        return self

    def step5(self) -> ty.Self:
        """Replace `subst1` by `subst2` in `work`."""
        s1 = self._unpad(self.subst1)
        s2 = self._unpad(self.subst2)
        self.work = self._check_and_pad(
            self._unpad(self.work).replace(s1, s2, 1))
        _logger.info('[step %d] work: %s', self.stepno, self.work)
        self._steps += 1
        return self
