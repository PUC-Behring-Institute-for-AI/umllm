#!/usr/bin/env python
# Copyright (C) 2026 PUC-Rio/PUC-Behring Institute for AI
# SPDX-License-Identifier: Apache-2.0

import pathlib

import click
import umllm


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
    '--min-cycles',
    type=int,
    default=0,
    help='Minimum number of cycles.')
@click.option(
    '--max-cycles',
    type=int,
    required=False,
    help='Maximum number of cycles.')
def main(
        n: int,
        states: int,
        symbols: int,
        work: int,
        min_cycles: int,
        max_cycles: int | None
) -> None:
    while n > 0:
        um = umllm.UM.random(
            states, symbols, work, min_cycles, max_cycles)
        path = pathlib.Path(f'{um.digest()}.txt')
        if path.exists():
            continue
        with open(path, 'wt', encoding='utf-8') as fp:
            print('#', states, symbols, work, min_cycles, max_cycles,
                  file=fp)
            print(um.dump(), file=fp)
        n -= 1

if __name__ == '__main__':
    main()
