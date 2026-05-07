# Copyright (C) 2026 PUC-Rio/PUC-Behring Institute for AI
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import pathlib
import sys

try:
    import click
except ImportError as err:
    raise ImportError(
        f'{__name__} requires click https://pypi.org/project/click/'
    ) from err

import typing_extensions as ty

from . import __description__, __version__
from .um import UM

_input = input
_logger: ty.Final[logging.Logger] = logging.getLogger(__name__)
_type = type


class CustomGroup(click.Group):
    def format_epilog(
            self,
            ctx: click.Context,
            formatter: click.HelpFormatter
    ) -> None:
        if self.epilog:
            formatter.write_paragraph()
            for line in self.epilog.split('\n'):
                formatter.write_text(line)


@click.group(
    cls=CustomGroup,
    help=f'UMLLM: {__description__}.',
    epilog='See <https://github.com/PUC-Behring-Institute-for-AI/umllm>')
@click.version_option(version=__version__)
def cli() -> None:
    pass


@cli.command(help='Start Flask app.')
@click.option(
    '-d', '--debug', 'debug',
    is_flag=True,
    default=False,
    help="Whether to enable Flask's debug mode.")
@click.option(
    '-p', '--port', 'port',
    type=int,
    default=5050,
    help='Server port.')
def flask(debug: bool, port: int) -> None:
    from .app import app as _app
    _app.run(port=port, debug=debug)


@cli.command(help='Start interactive shell.')
@click.option(
    '--input',
    type=str,
    required=False,
    help='UM input (override).')
@click.option(
    '--llm-model',
    type=str,
    default='gpt-5.4',
    help='LLM model to use.')
@click.option(
    '--llm-provider',
    type=str,
    default='openai',
    help='LLM provider use.')
@click.option(
    '--llm-seed',
    type=int,
    default=0,
    help='LLM seed')
@click.option(
    '--llm-temperature',
    type=float,
    default=0,
    help='LLM temperature')
@click.option(
    '--llm-truncate',
    type=int,
    required=False,
    help='Limit for the length of the message queue.')
@click.option(
    '--load', 'load',
    type=pathlib.Path,
    required=False,
    help='UM to load.')
@click.option(
    '--type', 'type',
    type=click.Choice(['llm', 'um']),
    default='um',
    help='UM type.')
@click.option(
    '--verbose', 'verbose',
    is_flag=True,
    default=False,
    help='Be verbose.')
def shell(
        input: str | None,
        llm_model: str,
        llm_provider: str,
        llm_seed: int,
        llm_temperature: float,
        llm_truncate: int | None,
        load: pathlib.Path | None,
        type: str,
        verbose: bool
) -> None:
    um: UM | None = None

    def reload() -> None:
        if load:
            nonlocal um
            um = _load(
                load,
                input=input,
                model=llm_model,
                provider=llm_provider,
                seed=llm_seed,
                temperature=llm_temperature,
                truncate=llm_truncate,
                type=type)
    if verbose:
        logging.basicConfig(level=logging.INFO)
    reload()
    while True:
        try:
            res = _input()
        except (EOFError, OSError):
            sys.exit(0)
        for cmd, *args in _parse(res):
            if cmd == '?' or 'help'.startswith(cmd):
                click.echo('''\
(h)elp           display this help
(q)uit           quit

(d)ump           dump UM contents
(l)oad FILE      load UM from file

(r)un [FUEL]     run UM until it halts or FUEL runs out
(c)ycle          cycle UM once
(n)ext           step UM once
(p)rev           revert last step
(R)eset          revert all steps
                ''')
            elif 'quit'.startswith(cmd):
                sys.exit(0)
            elif 'load'.startswith(cmd):
                if not args:
                    _error('missing FILE argument')
                    continue
                load = pathlib.Path(args[0])
                reload()
            else:
                if not um:
                    _error('no UM loaded')
                    continue
                assert um
                try:
                    if 'dump'.startswith(cmd):
                        click.echo(um)
                    elif 'run'.startswith(cmd):
                        if args:
                            um.run(int(args[0]))
                        else:
                            um.run()
                    elif 'cycle'.startswith(cmd):
                        um.cycle()
                    elif 'next'.startswith(cmd):
                        um.next()
                    elif 'prev'.startswith(cmd):
                        um.prev()
                    elif 'Reset'.startswith(cmd):
                        um.reset()
                    else:
                        _error('unknown command "%s", try "help"', cmd)
                except um.Error as err:
                    _error("%s", err)


def _load(path: pathlib.Path, **kwargs: ty.Any) -> UM:
    ty = kwargs.get('type', 'um')
    if ty == 'um':
        um: UM = UM.load_file(path)
    elif ty == 'llm':
        from .llm import UMLLM
        um = UMLLM.load_file(
            path,
            model=kwargs.get('model'),
            provider=kwargs.get('provider'),
            seed=kwargs.get('seed'),
            temperature=kwargs.get('temperature'),
            truncate=kwargs.get('truncate'))
    else:
        raise RuntimeError('should not get here')
    input = kwargs.get('input')
    if input:
        um.work = input
    return um


def _parse(input: str) -> ty.Iterator[ty.Iterable[str]]:
    if not input:
        yield ('dump',)
    else:
        for line in input.splitlines():
            for cmd in line.split(';'):
                yield cmd.split()


def _error(fmt: str, *args: ty.Any) -> None:
    print('error: ' + (fmt % args), file=sys.stderr)


if __name__ == '__main__':
    cli()
