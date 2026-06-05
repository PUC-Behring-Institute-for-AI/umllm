#!/usr/bin/env python
# Copyright (C) 2026 PUC-Rio/PUC-Behring Institute for AI
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import itertools
import json
import logging
import pathlib

import click
import pandas
import typing_extensions as ty

import umllm


@click.group()
def cli() -> None:
    pass


@cli.command(help='generate (equivalent) variants of machines')
@click.argument(
    'path',
    type=pathlib.Path,
    nargs=-1)
@click.option(
    '--outdir',
    type=pathlib.Path,
    default=pathlib.Path('.'),
    help='Output directory.')
def variant(
        outdir: pathlib.Path,
        path: ty.Sequence[pathlib.Path]
) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    for um in map(_um_gen_variant, path):
        Q, S, W, C, D, um = _um_read_stats(um)
        name = f'Q{Q:02d}-S{S:02d}-W{W:02d}-C{C:02d}-{D}.txt'
        um.dump_file(outdir / name)


def _um_gen_variant(
        path: pathlib.Path
) -> umllm.UM:
    um = umllm.UM.load_file(path)
    qs = um.get_machine_states()
    tr = {q: f'Q{(int(q[1:], 2) + len(qs)):b}' for q in qs}
    machine = [(tr[q0], s0, tr[q1], s1, m)  # type: ignore
               for q0, s0, q1, s1, m in um._parse_machine()]
    (wl, wq, wr) = um._parse_work()
    work = (wl, tr[wq], wr)
    halt = tr[um._parse_halt()]
    return umllm.UM(
        machine=''.join(''.join(t) for t in machine),
        halt=halt,
        work=''.join(work))


@cli.command(help='show information about machines')
@click.argument(
    'path',
    type=pathlib.Path,
    nargs=-1)
@click.option(
    '--outdir',
    type=pathlib.Path,
    required=False,
    help='Output directory.')
def info(
        outdir: pathlib.Path | None,
        path: ty.Sequence[pathlib.Path],
) -> None:
    df = _um_read_stats_as_dataframe(path, outdir)
    click.echo(df.to_string(index=False))
    click.echo()
    click.echo('== count ==')
    click.echo(df.count().to_string())
    click.echo()
    click.echo('== unique values ==')
    click.echo(df.apply(lambda col: col.unique()).to_string())


def _um_read_stats_as_dataframe(
        paths: ty.Iterable[pathlib.Path],
        outdir: pathlib.Path | None = None
) -> pandas.DataFrame:
    def it() -> ty.Iterable[dict[str, ty.Any]]:
        for Q, S, W, C, D, um in map(_um_read_stats, paths):
            if outdir:
                outdir.mkdir(parents=True, exist_ok=True)
                name = f'Q{Q:02d}-S{S:02d}-W{W:02d}-C{C:02d}-{D}.txt'
                um.dump_file(outdir / name)
            yield {'Q': Q, 'S': S, 'W': W, 'C': C, 'D': D}
    return pandas.DataFrame(it()).sort_values(
        by=['Q', 'S', 'W', 'C', 'D'])


def _um_read_stats(
        path_or_um: pathlib.Path | umllm.UM
) -> tuple[int, int, int, int, str, umllm.UM]:
    if isinstance(path_or_um, umllm.UM):
        um = path_or_um
    else:
        um = umllm.UM.load_file(path_or_um)
    Q = um.count_machine_states()
    S = um.count_machine_symbols(including_blanks=False)
    W = um.work_length(including_delimiting_blanks=False)
    um.run(1000)
    assert um.halted()
    C = um.cycles
    D = um.digest()
    return Q, S, W, C, D, um.reset()


@cli.command(help='evaluate machines using LLMs')
@click.argument(
    'provider',
    type=click.Choice([
        'deepseek',
        'google-genai',
        'ollama',
        'openai']))
@click.argument(
    'model',
    type=str)
@click.argument(
    'path',
    type=pathlib.Path,
    nargs=-1)
@click.option(
    '--log',
    type=pathlib.Path,
    required=False,
    help='Log info messages.')
@click.option(
    '--outdir',
    type=pathlib.Path,
    default=pathlib.Path('.'),
    help='Output directory.')
@click.option(
    '--prompt',
    type=str,
    multiple=True,
    help='Prompt.')
@click.option(
    '--seed',
    type=int,
    multiple=True,
    help='Seed.')
@click.option(
    '--temperature',
    type=float,
    multiple=True,
    help='Temperature.')
@click.option(
    '--truncate',
    type=int,
    multiple=True,
    help='Truncate.')
def evaluate(
        log: pathlib.Path | None,
        model: str,
        outdir: pathlib.Path,
        path: ty.Sequence[pathlib.Path],
        prompt: ty.Sequence[str],
        provider: str,
        seed: ty.Sequence[int],
        temperature: ty.Sequence[float],
        truncate: ty.Sequence[int],
) -> None:
    try:
        from tqdm import tqdm
    except ImportError:
        tqdm = (lambda x: x)    # type: ignore
    if log:
        if str(log) == '-':
            logging.basicConfig(level=logging.INFO)
        else:
            logging.basicConfig(filename=log, level=logging.INFO)
    prompt = prompt or ['simple-en']
    seed = seed or [0]
    temperature = temperature or [0.0]
    truncate = truncate or [-1]
    outdir.mkdir(parents=True, exist_ok=True)
    prod = list(itertools.product(path, prompt, temperature, seed, truncate))
    for path_, prompt_, temperature_, seed_, truncate_ in tqdm(prod):
        filename = (
            path_.stem
            + f'-{provider}'
            + f'-{model}'
            + f'-{prompt_}'
            + f'-temp{temperature_}'
            + f'-seed{seed_}'
            + (f'-tr{truncate_}' if truncate_ >= 0 else '')
            + '.json')
        outfile = outdir / filename
        if not outfile.exists():
            _evaluate(
                machine=path_,
                outfile=outfile,
                provider=provider,
                model=model,
                prompt=prompt_,
                temperature=temperature_,
                seed=seed_,
                truncate=truncate_ if truncate_ >= 0 else None)
        else:
            click.echo(f'skipping {outfile} (already exists)')


def _evaluate(
        machine: pathlib.Path,
        outfile: pathlib.Path,
        provider: str,
        model: str,
        prompt: str,
        temperature: float,
        seed: int,
        truncate: int | None
) -> None:
    Q, S, W, C, D, um = _um_read_stats(machine)
    system_prompt = umllm.UMLLM._load_prompt_template(prompt + '-system.txt')
    human_prompt = umllm.UMLLM._load_prompt_template(prompt + '-human.txt')
    llm = umllm.UMLLM.load_file(
        machine,
        provider=provider,
        model=model,
        system_prompt=system_prompt,
        human_prompt=human_prompt,
        temperature=temperature,
        seed=seed,
        truncate=truncate)
    assert llm.machine == um.machine
    assert llm.work == um.work
    results = {
        'machine_file': str(machine),
        'machine_dump': um.dump(),
        'num_states': Q,
        'num_symbols': S,
        'work_length': W,
        'cycles_until_halt': C,
        'digest': D,
        'provider': provider,
        'model': model,
        'prompt': prompt,
        'temperature': temperature,
        'seed': seed,
        'truncate': truncate,
        'messages': [],
        'cycles': 0,
        'error': None,
        'halted': None,
        'usage_metadata': None,
    }
    try:
        while not llm.halted():
            n = len(llm.messages or [])
            llm.cycle()
            assert isinstance(results['cycles'], int)
            results['cycles'] += 1
            assert llm.messages is not None
            assert len(llm.messages) >= n
            m = len(llm.messages) - n
            if m > 0:
                messages = llm.messages[-m:]
            assert isinstance(results['messages'], list)
            results['messages'] += list(map(lambda m: m.content, messages))
    except llm.Error as err:
        results['error'] = str(err)
    else:
        assert llm.work == um.run(1000).work
        results['halted'] = llm.halted()
    results['usage_metadata'] = llm.usage_metadata
    with open(outfile, 'wt', encoding='utf-8') as fp:
        json.dump(results, fp, indent=2)
        fp.write('\n')
        fp.flush()
    click.echo(f'wrote {outfile}')


if __name__ == '__main__':
    cli()
