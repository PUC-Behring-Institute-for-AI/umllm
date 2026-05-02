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
    '-a', '--app',
    is_flag=True,
    default='False',
    help='Start Flask app.')
@click.option(
    '-l', '--load',
    'load',
    type=pathlib.Path,
    metavar='PATH',
    help='UM to load.')
@click.option(
    '-v', '--verbose',
    'verbose',
    is_flag=True,
    default=False,
    help='Be verbose.')
@click.version_option(version=__version__)
def cli(app: bool, verbose: bool, load: pathlib.Path | None = None) -> None:
    if app:
        from .app import app as _app
        _app.run(port=5050, debug=True)
        sys.exit(0)
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
(q)uit           quit

(d)ump           dump UM contents
(l)oad <file>    load UM from file

(a)ll            step UM until it halts
(c)ycle          cycle UM once
(n)ext           step UM once
(p)rev           revert last step
(r)eset          revert all steps
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
            if 'dump'.startswith(cmd):
                click.echo(um)
            elif 'all'.startswith(cmd):
                um.run()
            elif 'cycle'.startswith(cmd):
                um.cycle()
            elif 'next'.startswith(cmd):
                um.next()
            elif 'prev'.startswith(cmd):
                um.prev()
            elif 'prev'.startswith(cmd):
                um.prev()
            elif 'reset'.startswith(cmd):
                um.reset()
            else:
                _error('unknown command "%s", try "help"', cmd)


def _error(fmt: str, *args: ty.Any) -> None:
    print('error: ' + (fmt % args), file=sys.stderr)


if __name__ == '__main__':
    cli()
