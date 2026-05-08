#!/usr/bin/env python
# Copyright (C) 2026 PUC-Rio/PUC-Behring Institute for AI
# SPDX-License-Identifier: Apache-2.0

import pathlib
import itertools

import click
import umllm
import typing_extensions as ty


@click.command()
@click.argument(
    'path',
    type=pathlib.Path,
    nargs=-1)
@click.option(
    '--outdir',
    type=pathlib.Path,
    default=pathlib.Path('.'),
    help='Output directory')
def evaluate(
        path: ty.Iterable[pathlib.Path],
        outdir: pathlib.Path
) -> None:
    model_provider = [
        ('openai', 'gpt-5.4'),
        ('openai', 'gpt-5.4-mini')]
    truncate = [None, 0]
    outdir.mkdir(parents=True, exist_ok=True)
    for p, (provider, model), truncate  in itertools.product(
            path, model_provider, truncate):
        tr = f'-T{truncate}' if truncate is not None else ''
        filename = p.stem + f'-{provider}-{model}{tr}.json'
        out = outdir / filename
        if not out.exists():
            _evaluate(out)
        else:
            print(f'skipping {out}')

def _evaluate(path: pathlib.Path) -> NOne:
    print('>>>', path)


if __name__ == '__main__':
    evaluate()
