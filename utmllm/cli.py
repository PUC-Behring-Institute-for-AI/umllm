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
from .utm import UTM

_logger: ty.Final[logging.Logger] = logging.getLogger(__name__)


@click.command(help=__description__ + '.')
@click.option(
    '-l', '--load',
    'load',
    type=pathlib.Path,
    metavar='PATH',
    help='UTM to load.',
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
    run: UTM.Run | None = None
    if load:
        run = UTM.load_file(load).run()
    while True:
        try:
            res = click.prompt(f'{__title__}')
        except Exception:
            break
        cmd, *args = res.split(' ')
        if 'help'.startswith(cmd):
            print('''\
(h)elp           display this help
(l)oad <file>    load UTM from file
(n)ext           executes the next step
(p)rint          print UTM state
(q)uit           quit
            ''')
        elif 'load'.startswith(cmd):
            if not args:
                print('error: missing <file> argument', file=sys.stderr)
                continue
            run = UTM.load_file(args[0]).run()
        elif 'next'.startswith(cmd):
            if not run:
                print('error: no UTM loaded', file=sys.stderr)
                continue
            run = next(run)
        elif 'print'.startswith(cmd):
            if not run:
                print('error: no UTM loaded', file=sys.stderr)
                continue
            click.echo(run)
        elif 'quit'.startswith(cmd):
            break
        else:
            print(f'error: unknown command "{cmd}", try "help"',
                  file=sys.stderr)


if __name__ == '__main__':
    cli()
