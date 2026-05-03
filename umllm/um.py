# Copyright (C) 2026 PUC-Rio/PUC-Behring Institute for AI
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import dataclasses
import json
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
    SYM_B: ty.Final[str] = '.'

    #: Left-movement indicator.
    SYM_L: ty.Final[str] = 'L'

    #: Right-movement indicator.
    SYM_R: ty.Final[str] = 'R'

    #: Ignored.
    SYM_X: ty.Final[str] = ' '

    _alphabet: ty.ClassVar[frozenset[Symbol]] =\
        frozenset([SYM_Q, SYM_S, SYM_0, SYM_1, SYM_B, SYM_L, SYM_R, SYM_X,])

    _tr: ty.ClassVar[dict[str, Symbol]] = {
        '_': SYM_B,
        'q': SYM_Q,
        's': SYM_S,
        '|': SYM_X,
        '₀': SYM_0,
        '₁': SYM_1,
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
    def check_tape(cls, value: ty.Any, pad: bool = False) -> Tape:
        """Coerces value to tape."""
        if isinstance(value, str):
            tape = ''.join(map(cls.check_symbol, value)).replace(cls.SYM_X, '')
            if pad:
                if tape:
                    left = '' if tape[0] == cls.SYM_B else cls.SYM_B
                    right = '' if tape[-1] == cls.SYM_B else cls.SYM_B
                    return left + tape + right
                else:
                    return cls.SYM_B + cls.SYM_B
            else:
                return tape
        else:
            raise ValueError(f'bad tape: {value}')

    class Error(Exception):
        """UM error."""

    @dataclasses.dataclass
    class Frame:
        """A UM frame (configuration)."""

        #: Transition table of the simulated machine.
        machine: Tape

        #: Halting state of the simulated machine.
        halt: Tape

        #: Work tape of the simulated machine.
        work: Tape

        #: Current state of the simulated machine.
        state: Tape

        #: Current symbol of the simulated machine (being read by head).
        symbol: Tape

        #: Symbol to the left of the head.
        left_symbol: Tape

        #: The state to transition to before moving the head.
        next_state: Tape

        #: The symbol to write before moving the head.
        next_symbol: Tape

        #: The direction to move the head next.
        next_move: Tape

        #: Substitution source (what to match in work).
        subst1: Tape

        #: Substitution target (what to replace `subst1` by in work).
        subst2: Tape

        #: Total number of steps executed.
        steps: int

        @classmethod
        def of_dict(cls, value: dict[str, ty.Any]) -> ty.Self:
            """Converts dictionary to frame."""
            return cls(
                machine=value['machine'],
                halt=value['halt'],
                work=value['work'],
                state=value['state'],
                symbol=value['symbol'],
                left_symbol=value['left_symbol'],
                next_state=value['next_state'],
                next_symbol=value['next_symbol'],
                next_move=value['next_move'],
                subst1=value['subst1'],
                subst2=value['subst2'],
                steps=value['steps'])

        def to_dict(self) -> dict[str, ty.Any]:
            """Converts frame to dictionary."""
            return {
                'machine': self.machine,
                'halt': self.halt,
                'work': self.work,
                'state': self.state,
                'symbol': self.symbol,
                'left_symbol': self.left_symbol,
                'next_state': self.next_state,
                'next_symbol': self.next_symbol,
                'next_move': self.next_move,
                'subst1': self.subst1,
                'subst2': self.subst2,
                'steps': self.steps}

    #: A stack of frames.
    _history: list[Frame]

    def __init__(
            self,
            machine: Tape | None = None,
            halt: Tape | None = None,
            work: Tape | None = None,
            state: Tape | None = None,
            symbol: Tape | None = None,
            left_symbol: Tape | None = None,
            next_state: Tape | None = None,
            next_symbol: Tape | None = None,
            next_move: Tape | None = None,
            subst1: Tape | None = None,
            subst2: Tape | None = None,
            steps: int | None = None,
            _empty: bool | None = None,
    ) -> None:
        self._history = [self.Frame(
            machine=self.check_tape(machine or ''),
            halt=self.check_tape(halt or ''),
            work=self.check_tape(work or '', pad=True),
            state=self.check_tape(state or ''),
            symbol=self.check_tape(symbol or ''),
            left_symbol=self.check_tape(left_symbol or ''),
            next_state=self.check_tape(next_state or ''),
            next_symbol=self.check_tape(next_symbol or ''),
            next_move=self.check_tape(next_move or ''),
            subst1=self.check_tape(subst1 or ''),
            subst2=self.check_tape(subst2 or ''),
            steps=abs(steps or 0))]
        if not _empty:
            _logger.info('[init] machine: %s', self.machine)
            _logger.info('[init] halt: %s', self.halt)
            _logger.info('[init] work: %s', self.work)

    def __str__(self) -> str:
        t = self.frame.to_dict()
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
    def frame(self) -> Frame:
        return self._history[-1]

    @property
    def machine(self) -> Tape:
        return self.frame.machine

    @machine.setter
    def machine(self, s: Tape) -> None:
        self.frame.machine = self.check_tape(s)

    @property
    def halt(self) -> Tape:
        return self.frame.halt

    @halt.setter
    def halt(self, s: Tape) -> None:
        self.frame.halt = self.check_tape(s)

    @property
    def work(self) -> Tape:
        return self.frame.work

    @work.setter
    def work(self, s: Tape) -> None:
        self.frame.work = self.check_tape(s, pad=True)

    @property
    def state(self) -> Tape:
        return self.frame.state

    @state.setter
    def state(self, s: Tape) -> None:
        self.frame.state = self.check_tape(s)

    @property
    def symbol(self) -> Tape:
        return self.frame.symbol

    @symbol.setter
    def symbol(self, s: Tape) -> None:
        self.frame.symbol = self.check_tape(s)

    @property
    def left_symbol(self) -> Tape:
        return self.frame.left_symbol

    @left_symbol.setter
    def left_symbol(self, s: Tape) -> None:
        self.frame.left_symbol = self.check_tape(s)

    @property
    def next_state(self) -> Tape:
        return self.frame.next_state

    @next_state.setter
    def next_state(self, s: Tape) -> None:
        self.frame.next_state = self.check_tape(s)

    @property
    def next_symbol(self) -> Tape:
        return self.frame.next_symbol

    @next_symbol.setter
    def next_symbol(self, s: Tape) -> None:
        self.frame.next_symbol = self.check_tape(s)

    @property
    def next_move(self) -> Tape:
        return self.frame.next_move

    @next_move.setter
    def next_move(self, s: Tape) -> None:
        self.frame.next_move = self.check_tape(s)

    @property
    def subst1(self) -> Tape:
        return self.frame.subst1

    @subst1.setter
    def subst1(self, s: Tape) -> None:
        self.frame.subst1 = self.check_tape(s)

    @property
    def subst2(self) -> Tape:
        return self.frame.subst2

    @subst2.setter
    def subst2(self, s: Tape) -> None:
        self.frame.subst2 = self.check_tape(s)

    @property
    def steps(self) -> int:
        return self.frame.steps

    @steps.setter
    def steps(self, n: int) -> None:
        self.frame.steps = n

    @property
    def prev_step(self) -> int | None:
        """The last step executed (1-6 or `None`)."""
        return ((self.steps - 1) % 6) + 1 if self.steps else None

    @property
    def next_step(self) -> int | None:
        """The next step to be executed (1-6 or `None`)."""
        return (self.steps % 6) + 1 if not self.halted() else None

    @property
    def cycles(self) -> int:
        """The total number of cycles executed."""
        return self.steps // 6

    @classmethod
    def of_dict(cls, value: dict[str, ty.Any]) -> ty.Self:
        """Converts dictionary to UM."""
        um = cls(_empty=True)
        um._history = [cls.Frame.of_dict(t) for t in value['_history']]
        return um

    def to_dict(self) -> dict[str, ty.Any]:
        """Converts UM to dictionary."""
        return {'_history': [frame.to_dict() for frame in self._history]}

    @classmethod
    def of_json(cls, s: str, **kwargs: ty.Any) -> ty.Self:
        """Converts JSON string to UM."""
        return cls.of_dict(json.loads(s))

    def to_json(self, **kwargs: ty.Any) -> str:
        """Converts UM to JSON string."""
        return json.dumps(self.to_dict(), **kwargs)

    @classmethod
    def load(cls, s: str) -> ty.Self:
        """Loads UM from string."""
        machine: str = ''
        halt: str = ''
        work: str = ''
        it = filter(lambda x: not x.startswith('#'),
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

    def _tape2html(self, tape: Tape) -> str:
        def it(input: str) -> ty.Iterator[str]:
            import html
            while input:
                c = input[0]
                if c == self.SYM_Q or c == self.SYM_S:
                    m = re.match(f'({self._re01s})', input[1:])
                    if m:
                        k = 'Q' if c == self.SYM_Q else 'S'
                        s = html.escape(m.group(1))
                        yield f'<span class="{k}">{html.escape(c)}'
                        yield f'<sub>{s}</sub></span>'
                        input = input[len(s):]
                        continue
                elif c == self.SYM_B:
                    yield '<span class="B">⋅</span>'
                elif c == self.SYM_L:
                    yield f'<span class="L">{html.escape(c)}</span>'
                elif c == self.SYM_R:
                    yield f'<span class="R">{html.escape(c)}</span>'
                input = input[1:]
        return ''.join(it(tape))

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
            f'({self._reSn}*)'
            + f'({self._reQn})'
            + f'({self._reSn}*)',
            self.work)
        if m is None:
            raise self.Error(f'bad work: {self.work}')
        return m.groups()       # type: ignore

    def reset(self) -> ty.Self:
        """Resets UM to its initial frame."""
        _logger.info('[reset]')
        self._history = self._history[:1]
        return self

    def run(self) -> ty.Self:
        """Executes step cycles until the halting state is reached."""
        if not self.halted():
            _logger.info('[run]')
        while not self.halted():
            self.cycle()
        return self

    def cycle(self) -> ty.Self:
        """Executes one cycle of steps."""
        if not self.halted():
            _logger.info('[cycle %d]', self.cycles)
        while not self.halted():
            self.next()
            if self.next_step == 1:
                break
        return self

    def prev(self) -> ty.Self:
        """Reverts the last executed step."""
        if self.prev_step is not None:
            _logger.info('[prev]')
            assert len(self._history) > 1, len(self._history)
            self._history.pop()
        return self

    def next(self) -> ty.Self:
        """Executes the next step."""
        if self.next_step is not None:
            return getattr(self, f'step{self.next_step}')()
        return self

    def halted(self) -> bool:
        """Tests whether UM has halted."""
        m = re.search(f'({self._reQn})', self.work)
        return m is not None and self.halt == m.group(1)

    def step1(self) -> ty.Self:
        """Load `state` and `symbol`."""
        m = re.search(f'({self._reQn})({self._reSn})', self.work)
        if m is None:
            raise self.Error(f'bad work: {self.work}')
        f = self._next_frame()
        f.state = self.check_tape(m.group(1))
        f.symbol = self.check_tape(m.group(2))
        _logger.info('[step 1] state: %s', f.state)
        _logger.info('[step 1] symbol: %s', f.symbol)
        return self._push_frame(f)

    def step2(self) -> ty.Self:
        """Load `left_symbol`."""
        m = re.search(rf'({self._reSn}){self._reQn}', self.work)
        f = self._next_frame()
        f.left_symbol = self.check_tape(
            m.group(1) if m is not None else '')
        _logger.info('[step 2] left symbol: %s', f.left_symbol)
        return self._push_frame(f)

    def step3(self) -> ty.Self:
        """Load `next_state`, `next_symbol`, and `next_move`."""
        m = re.search(
            f'{self.state}{self.symbol}'
            f'({self._reQn})({self._reSn})({self._reLR})',
            self.machine)
        if m is None:
            raise self.Error(f'bad machine: {self.machine}')
        next_state, next_symbol, next_move = m.groups()  # type: ignore
        f = self._next_frame()
        f.next_state = self.check_tape(next_state)
        f.next_symbol = self.check_tape(next_symbol)
        f.next_move = self.check_tape(next_move)
        _logger.info('[step 3] next state: %s', f.next_state)
        _logger.info('[step 3] next symbol: %s', f.next_symbol)
        _logger.info('[step 3] next move: %s', f.next_move)
        return self._push_frame(f)

    def step4(self) -> ty.Self:
        """Load `subst1`."""
        f = self._next_frame()
        if self.next_move == self.SYM_L:
            f.subst1 = self.check_tape(
                self.left_symbol + self.state + self.symbol)
        elif self.next_move == self.SYM_R:
            f.subst1 = self.check_tape(self.state + self.symbol)
        else:
            raise self.Error(f'bad next_move: {self.next_move}')
        _logger.info('[step 4] subst1: %s', f.subst1)
        return self._push_frame(f)

    def step5(self) -> ty.Self:
        """Load `subst2`"""
        f = self._next_frame()
        if self.next_move == self.SYM_L:
            f.subst2 = self.check_tape(
                self.next_state + self.left_symbol + self.next_symbol)
        elif self.next_move == self.SYM_R:
            f.subst2 = self.check_tape(self.next_symbol + self.next_state)
        else:
            raise self.Error(f'bad next_move: {self.next_move}')
        _logger.info('[step 5] subst2: %s', f.subst2)
        return self._push_frame(f)

    def step6(self) -> ty.Self:
        """Replace `subst1` by `subst2` in `work`."""
        f = self._next_frame()
        f.work = self.check_tape(self.work.replace(
            self.subst1, self.subst2, 1), pad=True)
        _logger.info('[step 6] work: %s', f.work)
        return self._push_frame(f)

    def _next_frame(self) -> Frame:
        return dataclasses.replace(self.frame, steps=self.frame.steps + 1)

    def _push_frame(self, frame: Frame) -> ty.Self:
        self._history.append(frame)
        return self
