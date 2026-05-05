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

from . import __description__, __title__, __version__
from .um import UM

_logger: ty.Final[logging.Logger] = logging.getLogger(__name__)


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
    '-i', '--input', 'input',
    type=str,
    required=False,
    help='UM input (override).')
@click.option(
    '-l', '--load', 'load',
    type=pathlib.Path,
    required=False,
    help='UM to load.')
@click.option(
    '-m', '--model', 'model',
    type=str,
    default='gpt-5.4',
    help='LLM model to use.')
@click.option(
    '-t', '--type', 'type',
    type=click.Choice(['um', 'llm']),
    default='um',
    help='UM type.')
@click.option(
    '-v', '--verbose', 'verbose',
    is_flag=True,
    default=False,
    help='Be verbose.')
def shell(
        input: str | None,
        load: pathlib.Path | None,
        model: str,
        type: str,
        verbose: bool
) -> None:
    if verbose:
        logging.basicConfig(level=logging.INFO)
    um: UM | None = None
    if load:
        if type == 'um':
            um = UM.load_file(load)
        elif type == 'llm':
            from .llm import UMLLM
            um = UMLLM.load_file(
                load,
                provider='openai',
                model=model,
                temperature=0.,
                seed=0)
        else:
            raise RuntimeError('should not get here')
        if input:
            um.work = input
    while True:
        try:
            res = click.prompt(f'{__title__}', default='dump')
        except Exception:
            break
        cmd, *args = res.split(' ')
        if cmd == '?' or 'help'.startswith(cmd):
            print('''\
(h)elp           display this help
(q)uit           quit

(d)ump           dump UM contents
(l)oad <file>    load UM from file

(r)un            run UM until it halts
(c)ycle          cycle UM once
(n)ext           step UM once
(p)rev           revert last step
(R)eset          revert all steps
            ''')
        elif 'quit'.startswith(cmd):
            break
        elif 'load'.startswith(cmd):
            if not args:
                _error('missing <file> argument')
                continue
            um = UM.load_file(args[0])
        else:
            if not um:
                _error('no UM loaded')
                continue
            assert um
            try:
                if 'dump'.startswith(cmd):
                    click.echo(um)
                elif 'run'.startswith(cmd):
                    um.run()
                elif 'cycle'.startswith(cmd):
                    um.cycle()
                elif 'next'.startswith(cmd):
                    um.next()
                elif 'prev'.startswith(cmd):
                    um.prev()
                elif 'prev'.startswith(cmd):
                    um.prev()
                elif 'Reset'.startswith(cmd):
                    um.reset()
                else:
                    _error('unknown command "%s", try "help"', cmd)
            except um.Error as err:
                _error("%s", err)


def _error(fmt: str, *args: ty.Any) -> None:
    print('error: ' + (fmt % args), file=sys.stderr)


if __name__ == '__main__':
    cli()
