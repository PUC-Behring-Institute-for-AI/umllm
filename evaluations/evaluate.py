#!/usr/bin/env python
# Copyright (C) 2026 PUC-Rio/PUC-Behring Institute for AI
# SPDX-License-Identifier: Apache-2.0

import itertools
import json
import logging
import pathlib
import re

import click
import umllm
import typing_extensions as ty


MODEL_PROVIDER: ty.Final[ty.Sequence[tuple[str, str]]] = [
    ('google-genai', 'gemini-3.1-pro-preview'),
    # ('openai', 'gpt-5.4'),
    # ('openai', 'gpt-5.4-mini'),
]

PROMPT: ty.Final[ty.Sequence[tuple[str, str, str]]] = [
    ('detailed-en', 'detailed-en-system.txt', 'detailed-en-human.txt'),
    ('simple-pt', 'simple-pt-system.txt', 'simple-pt-human.txt'),
]

TEMPERATURE: ty.Final[ty.Sequence[float]] = [0.]

SEED: ty.Final[ty.Sequence[int]] = [0]

TRUNCATE: ty.Final[ty.Sequence[int | None]] = [None, 0]

logging.basicConfig(filename='evaluate.log', level=logging.INFO)


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
    try:
        from tqdm import tqdm
    except ImportError:
        tqdm = (lambda x: x)
    outdir.mkdir(parents=True, exist_ok=True)
    prod = list(itertools.product(
        path, MODEL_PROVIDER, PROMPT, TEMPERATURE, SEED, TRUNCATE))
    for p, (provider, model), prompt, temp, seed, truncate in tqdm(prod):
        tr = f'-tr{truncate}' if truncate is not None else ''
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
                truncate=truncate)
        else:
            print('skipping', out)


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
    um = umllm.UM.load_file(machine)
    um_initial_work = um.work
    xQ = um.count_machine_states()
    xS = um.count_machine_symbols(including_blanks=False)
    xW = um.work_length(including_delimiting_blanks=False)
    um.run(1000)
    assert um.halted()
    xC = um.cycles
    xD = um.digest()
    m = _re_machine_stem.match(machine.stem)
    if m is None:
        raise RuntimeError(f'cannot parse machine filename: {machine}')
    t = m.groups()
    yQ, yS, yW, yC = map(int, t[:-1])
    yD = t[-1]
    x = (xQ, xS, xW, xC, xD)
    y = (yQ, yS, yW, yC, yD)
    if x != y:
        raise RuntimeError(f'machine spec mismatch: {x} != {y}')
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
    assert llm.halt == um.halt
    assert llm.work == um_initial_work
    results = {
        'machine_file': str(machine),
        'machine_dump': um.dump(),
        'num_states': xQ,
        'num_symbols': xS,
        'work_length': xW,
        'cycles_until_halt': xC,
        'digest': xD,
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
    print('wrote', outfile)


if __name__ == '__main__':
    evaluate()
