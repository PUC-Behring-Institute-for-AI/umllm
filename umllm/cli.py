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


@click.command(help=__description__ + '.')
@click.option(
    '-l', '--load',
    'load',
    type=pathlib.Path,
    metavar='PATH',
    help='UM to load.',
)
@click.option(
    '-v', '--verbose',
    'verbose',
    is_flag=True,
    default=False,
    help='Be verbose.',
)
@click.version_option(version=__version__)
def cli(verbose: bool, load: pathlib.Path | None = None) -> None:
    if verbose:
        logging.basicConfig(level=logging.INFO)
    um: UM | None = None
    if load:
        um = UM.load_file(load)
    while True:
        try:
            res = click.prompt(f'{__title__}')
        except Exception:
            break
        cmd, *args = res.split(' ')
        if 'help'.startswith(cmd):
            print('''\
(h)elp           display this help
(l)oad <file>    load UM from file
(p)rint          print UM state
(r)un            run until UM halts
(c)ycle          cycle UM once
(s)tep           step UM once
(q)uit           quit
            ''')
        elif 'load'.startswith(cmd):
            if not args:
                _error('missing <file> argument')
                continue
            um = UM.load_file(args[0])
        elif 'print'.startswith(cmd):
            if not um:
                _error('no UM loaded')
                continue
            click.echo(um)
        elif 'run'.startswith(cmd):
            if not um:
                _error('no UM loaded')
                continue
            um.run()
        elif 'cycle'.startswith(cmd):
            if not um:
                _error('no UM loaded')
                continue
            um.cycle()
        elif 'step'.startswith(cmd):
            if not um:
                _error('no UM loaded')
                continue
            um.step()
        elif 'quit'.startswith(cmd):
            break
        else:
            _error('unknown command "%s", try "help"', cmd)


def _error(fmt: str, *args: ty.Any) -> None:
    print('error: ' + (fmt % args), file=sys.stderr)


if __name__ == '__main__':
    cli()
