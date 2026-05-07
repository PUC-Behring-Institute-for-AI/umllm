# Copyright (C) 2026 PUC-Rio/PUC-Behring Institute for AI
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import dataclasses
import itertools
import json
import logging
import pathlib
import random
import re

import typing_extensions as ty

Symbol: ty.TypeAlias = str
Tape: ty.TypeAlias = str

_logger: ty.Final[logging.Logger] = logging.getLogger(__name__)


class UM:
    """Universal Machine."""

    #: State of the simulated machine (delimiter).
    SYM_Q: ty.Final[str] = 'Q'

    #: Symbol of the simulated machine (delimiter).
    SYM_S: ty.Final[str] = 'S'

    #: The digit "0".
    SYM_0: ty.Final[str] = '0'

    #: The digit "1".
    SYM_1: ty.Final[str] = '1'

    #: The digit "2".
    SYM_2: ty.Final[str] = '2'

    #: The digit "3".
    SYM_3: ty.Final[str] = '3'

    #: The digit "4".
    SYM_4: ty.Final[str] = '4'

    #: The digit "5".
    SYM_5: ty.Final[str] = '5'

    #: The digit "6".
    SYM_6: ty.Final[str] = '6'

    #: The digit "7".
    SYM_7: ty.Final[str] = '7'

    #: The digit "8".
    SYM_8: ty.Final[str] = '8'

    #: The digit "9".
    SYM_9: ty.Final[str] = '9'

    #: The blank symbol.
    SYM_B: ty.Final[str] = '.'

    #: Left-movement indicator.
    SYM_L: ty.Final[str] = 'L'

    #: Right-movement indicator.
    SYM_R: ty.Final[str] = 'R'

    #: Ignored.
    SYM_X: ty.Final[str] = ' '

    _alphabet: ty.ClassVar[frozenset[Symbol]] =\
        frozenset([SYM_Q, SYM_S, SYM_0, SYM_1, SYM_2, SYM_3,
                   SYM_4, SYM_5, SYM_6, SYM_7, SYM_8, SYM_9,
                   SYM_B, SYM_L, SYM_R, SYM_X,])

    _tr: ty.ClassVar[dict[str, Symbol]] = {
        'q': SYM_Q,
        's': SYM_S,
        '₀': SYM_0,
        '₁': SYM_1,
        '₂': SYM_2,
        '₃': SYM_3,
        '₄': SYM_4,
        '₅': SYM_5,
        '₆': SYM_6,
        '₇': SYM_7,
        '₈': SYM_8,
        '₉': SYM_9,
        '_': SYM_B,
        '<': SYM_L,
        '>': SYM_R,
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

    @classmethod
    def random_Q(cls, num_states: int) -> Tape:
        """Generates a random tape containing a single state."""
        return f'{cls.SYM_Q}{random.randrange(0, num_states):b}'

    @classmethod
    def random_S(cls, num_symbols: int) -> Tape:
        """Generates a random tape containing a single symbol."""
        return f'{cls.SYM_S}{random.randrange(0, num_symbols):b}'

    @classmethod
    def random_S_or_B(cls, num_symbols: int) -> Tape:
        """Generates a random tape containing a single symbol or blank."""
        i = random.randint(0, num_symbols)
        if i < num_symbols:
            return f'{cls.SYM_S}{i:b}'
        else:
            return cls.SYM_B

    @classmethod
    def random_move(cls) -> Tape:
        """Generates a random tape containing either "L" or "R"."""
        return cls.SYM_L if bool(random.randint(0, 1)) else cls.SYM_R

    @classmethod
    def random_machine_tape(cls, num_states: int, num_symbols: int) -> Tape:
        """Generates a random machine tape."""
        def it() -> ty.Iterator[str]:
            for q0, s0 in itertools.product(
                    range(num_states), range(num_symbols + 1)):
                yield f'{cls.SYM_Q}{q0:b}'
                if s0 < num_symbols:
                    yield f'{cls.SYM_S}{s0:b}'
                else:
                    yield cls.SYM_B
                yield cls.random_Q(num_states)
                yield cls.random_S_or_B(num_symbols)
                yield cls.random_move()
        return cls.check_tape(''.join(it()))

    @classmethod
    def random_halt_tape(cls, num_states: int) -> Tape:
        """Generates a random halt tape."""
        return cls.random_Q(num_states)

    @classmethod
    def random_work_tape(
            cls,
            num_states: int,
            num_symbols: int,
            length: int
    ) -> Tape:
        """Generates a random work tape."""
        def it() -> ty.Iterator[str]:
            if length:
                head_position = random.randrange(length)
                for pos in range(length):
                    if pos == head_position:
                        yield cls.random_Q(num_states)
                    yield cls.random_S(num_symbols)
        return cls.check_tape(''.join(it()), pad=True)

    @classmethod
    def random(
            cls,
            num_states: int,
            num_symbols: int,
            length: int | None = None,
            min_cycles: int | None = None,
            max_cycles: int | None = None
    ) -> ty.Self:
        um: UM | None = None
        length = length if length is not None else 0
        min_cycles = min_cycles if min_cycles is not None else 0
        assert min_cycles >= 0
        max_cycles =\
            max_cycles if max_cycles is not None else cls._default_run_fuel
        assert max_cycles >= min_cycles
        while True:
            um = cls(cls.random_machine_tape(num_states, num_symbols),
                     cls.random_halt_tape(num_states),
                     cls.random_work_tape(num_states, num_symbols, length))
            if length == 0 or min_cycles == 0:
                return um
            else:
                um.run(max_cycles)
                assert um.cycles <= max_cycles
                if um.halted() and um.cycles >= min_cycles:
                    return um.reset()

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
        t['cycles'] = self.cycles
        t['history'] = len(self._history)
        t['halted'] = self.halted()
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

    def digest(self) -> str:
        """Computes a digest using UM's machine and halt tapes."""
        import hashlib
        return hashlib.sha256((self.machine + self.halt).encode(
            'utf-8')).hexdigest()

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

    def dump(self) -> str:
        """Dumps UM machine, halt, and work to string."""
        return f'{self.machine}\n\n{self.halt}\n\n{self.work[1:-1]}'

    def dump_file(self, path: pathlib.Path | str) -> None:
        """Dumps UM machine, halt, and work to file."""
        with open(pathlib.Path(path), 'wt', encoding='utf-8') as fp:
            print(self.dump(), file=fp)

    @classmethod
    def load(cls, s: str, **kwargs: ty.Any) -> ty.Self:
        """Loads UM machine, halt, and work from string."""
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
        return cls(machine, halt, work, **kwargs)

    @classmethod
    def load_file(cls, path: pathlib.Path | str, **kwargs: ty.Any) -> ty.Self:
        """Loads UM machine, halt, and work from file."""
        with open(pathlib.Path(path), 'rt', encoding='utf-8') as fp:
            return cls.load(fp.read(), **kwargs)

    @property
    def _re09(self) -> str:
        return '[0-9]'

    @property
    def _re09s(self) -> str:
        return self._re09 + '+'

    @property
    def _reQn(self) -> str:
        return re.escape(self.SYM_Q) + self._re09s

    @property
    def _reSn(self) -> str:
        return ('(?:'
                + re.escape(self.SYM_S) + self._re09s + '|'
                + re.escape(self.SYM_B) + ')')

    @property
    def _reLR(self) -> str:
        return '[' + re.escape(self.SYM_L) + re.escape(self.SYM_R) + ']'

    def _tape2html(self, tape: Tape) -> str:
        def it(input: str) -> ty.Iterator[str]:
            import html
            while input:
                c = input[0]
                if c == self.SYM_Q or c == self.SYM_S:
                    m = re.match(f'({self._re09s})', input[1:])
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
            f'({self._reSn}+)'
            + f'({self._reQn})'
            + f'({self._reSn}+)', self.work)
        if m is None:
            raise self.Error(f'bad work: {self.work}')
        return m.groups()       # type: ignore

    def reset(self) -> ty.Self:
        """Resets UM to its initial frame."""
        _logger.info('[reset]')
        self._history = self._history[:1]
        return self

    _default_run_fuel: ty.ClassVar[int] = 100

    def run(self, fuel: int | None = None) -> ty.Self:
        """Executes step cycles until halting state is reached or fuel (in
        number of cycles) is exhausted."""
        fuel = fuel if fuel is not None else self._default_run_fuel
        assert fuel is not None
        while True:
            if self.halted():
                _logger.info('[run] halted')
                break
            if fuel == 0:
                _logger.info('[run] no more fuel')
                break
            assert fuel > 0
            _logger.info('[run] fuel: %d', fuel)
            self.cycle()
            fuel -= 1
        return self

    def cycle(self) -> ty.Self:
        """Executes one cycle of steps."""
        if not self.halted():
            _logger.info('[cycle %d]', self.cycles)
        while True:
            if self.halted():
                _logger.info('[cycle %d] halted', self.cycles)
                break
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
            f'{re.escape(self.state)}{re.escape(self.symbol)}'
            f'({self._reQn})({self._reSn})({self._reLR})',
            self.machine)
        if m is None:
            raise self.Error(f'no transition for: {self.state}{self.symbol}')
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
