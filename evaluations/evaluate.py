#!/usr/bin/env python
# Copyright (C) 2026 PUC-Rio/PUC-Behring Institute for AI
# SPDX-License-Identifier: Apache-2.0

import itertools
import json
import logging
import pathlib
import re

import click
import pandas
import typing_extensions as ty
import umllm


PROVIDER_MODEL: ty.Final[ty.Sequence[tuple[str, str]]] = [
    #('deepseek', 'deepseek-v4-pro'),
    #('google-genai', 'gemini-3.1-pro-preview'),
    #('openai', 'gpt-5.2'),
    # ('openai', 'gpt-5.4'),
    #('openai', 'gpt-5.4-mini'),
]

PROMPT: ty.Final[ty.Sequence[tuple[str, str, str]]] = [
    ('simple-en', 'simple-en-system.txt', 'simple-en-human.txt'),
    # ('detailed-en', 'detailed-en-system.txt', 'detailed-en-human.txt'),
    # ('simple-pt', 'simple-pt-system.txt', 'simple-pt-human.txt'),
]

TEMPERATURE: ty.Final[ty.Sequence[float]] = [0.]

SEED: ty.Final[ty.Sequence[int]] = [0]

TRUNCATE: ty.Final[ty.Sequence[int | None]] = [None, 0]

logging.basicConfig(filename='evaluate.log', level=logging.INFO)


@click.group()
def cli() -> None:
    pass


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
        path: pathlib.Path
) -> tuple[int, int, int, int, str, umllm.UM]:
    um = umllm.UM.load_file(path)
    um_initial_work = um.work
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
    '--outdir',
    type=pathlib.Path,
    default=pathlib.Path('.'),
    help='Output directory')
@click.option(
    '--seed',
    type=int,
    multiple=True,
    help='Seed.')
@click.option(
    '--show',
    is_flag=True,
    default=False,
    help='Show statistics of the input machines.')
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
        model: str,
        outdir: pathlib.Path,
        path: ty.Sequence[pathlib.Path],
        provider: str,
        seed: ty.Sequence[int],
        temperature: ty.Sequence[float],
        truncate: ty.Sequence[int]
) -> None:
    try:
        from tqdm import tqdm
    except ImportError:
        tqdm = (lambda x: x)
    seed = seed or [0]
    temperature = temperature or [0.0]
    truncate = truncate or [-1]
    outdir.mkdir(parents=True, exist_ok=True)
    prod = list(itertools.product(
        path, provider, model, prompt, temperature, seed, truncate))
    for p, provider, model, prompt, temp, seed, truncate in tqdm(prod):
        tr = f'-tr{truncate}' if truncate >= 0 else ''
        filename = (
            p.stem
            + f'-{provider}'
            + f'-{model}'
            + f'-{prompt[0]}'
            + f'-temp{temp}'
            + f'-seed{seed}'
            + f'{tr}.json')
        out = outdir / filename
        if not out.exists():
            _evaluate(
                machine=p,
                outfile=out,
                provider=provider,
                model=model,
                prompt=prompt,
                temperature=temp,
                seed=seed,
                truncate=truncate if truncate >= 0 else None)
        else:
            click.echo('skipping', out)


_re_machine_stem: ty.Final[re.Pattern[str]] = re.compile(
    r'^Q(\d+)-S(\d+)-W(\d+)-C(\d+)-([a-f0-9]+)$')


def _evaluate(
        machine: pathlib.Path,
        outfile: pathlib.Path,
        provider: str,
        model: str,
        prompt: tuple[str, str, str],
        temperature: float,
        seed: int,
        truncate: int | None
) -> None:
    Q, S, W, C, D, um = _um_read_stats(machine)
    system_prompt = umllm.UMLLM._load_prompt_template(prompt[1])
    human_prompt = umllm.UMLLM._load_prompt_template(prompt[2])
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
        'prompt': prompt[0],
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
            results['cycles'] += 1
            assert len(llm.messages) >= n
            m = len(llm.messages) - n
            if m > 0:
                messages = llm.messages[-m:]
            results['messages'] += list(map(lambda m: m.content, messages))
    except llm.Error as err:
        results['error'] = str(err)
    else:
        assert llm.work == um.work
        results['halted'] = llm.halted()
    results['usage_metadata'] = llm.usage_metadata
    with open(outfile, 'wt', encoding='utf-8') as fp:
        json.dump(results, fp, indent=2)
        fp.write('\n')
        fp.flush()
    click.echo('wrote', outfile)




if __name__ == '__main__':
    cli()
