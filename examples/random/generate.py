#!/usr/bin/env python
# Copyright (C) 2026 PUC-Rio/PUC-Behring Institute for AI
# SPDX-License-Identifier: Apache-2.0

import itertools
import pathlib
import re

import click
import umllm
import typing_extensions as ty

_re_digest: ty.Final[re.Pattern[str]] = re.compile(r'^.*-([a-f0-9]+)\.txt$')


@click.command()
@click.argument(
    'n',
    type=int,
    default=1)
@click.option(
    '--states',
    type=int,
    default=2,
    help='Number of states.')
@click.option(
    '--symbols',
    type=int,
    default=2,
    help='Number of symbols.')
@click.option(
    '--work',
    type=int,
    default=10,
    help='Length of the work tape.')
@click.option(
    '--cycles',
    type=int,
    default=10,
    help='Number of cycles.')
@click.option(
    '--preset',
    is_flag=True,
    default=False,
    help='Preset generation.')
def generate(
        n: int,
        states: int,
        symbols: int,
        work: int,
        cycles: int,
        preset: bool
) -> None:
    if preset:
        Qs = (2, 16, 32)
        Ss = (2, 16, 32)
        Ws = (8, 16, 32, 64)
        Cs = range(5, 105, 5)
        prod = list(itertools.product(Qs, Ss, Ws, Cs))
        for i, (q, s, w, c) in enumerate(prod, 1):
            print(f'# {i}/{len(prod)}')
            seen = set(pathlib.Path('.').glob(
                f'Q{q:02d}-S{s:02d}-W{w:02d}-C{c:02d}-*.txt'))
            if len(seen) < 5:
                _generate(5 - len(seen), q, s, w, c)
    else:
        _generate(n, states, symbols, work, cycles)


def _generate(
        n: int,
        states: int,
        symbols: int,
        work: int,
        cycles: int,
) -> None:
    seen = {_re_digest.match(p.name).group(1)
            for p in pathlib.Path('.').glob('Q*-S*-W*-C*-*.txt')}
    Q, S, W, C = states, symbols, work, cycles
    while n > 0:
        um = umllm.UM.random(Q, S, W, C, C)
        digest = um.digest()
        if digest in seen:
            click.echo(f'skipping {digest}')
            continue
        path = pathlib.Path(
            f'Q{Q:02d}-S{S:02d}-W{W:02d}-C{C:02d}-{digest}.txt')
        with open(path, 'wt', encoding='utf-8') as fp:
            print('# Q%d S%d W%d C%d %s' % (Q, S, W, C, digest), file=fp)
            print(um.dump(), file=fp)
        click.echo(f'wrote {path}')
        n -= 1

if __name__ == '__main__':
    generate()
