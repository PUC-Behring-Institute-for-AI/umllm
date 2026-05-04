# Copyright (C) 2026 PUC-Rio/PUC-Behring Institute for AI
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re

import typing_extensions as ty
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate

from .um import _logger, Tape, UM


class UMLLM(UM):
    """Universal Machine backed by an LLM."""

    @staticmethod
    def _load_prompt_template(
            filename: str,
            format: str = 'mustache'
    ) -> PromptTemplate:
        import importlib
        with importlib.resources.path(  # pyright: ignore
                'umllm.prompts') as dir:
            return PromptTemplate.from_file(
                dir / filename, template_format=format)

    #: The default system prompt.
    _default_system_prompt: ty.ClassVar[PromptTemplate] =\
        _load_prompt_template('system.md')

    #: The default human prompt.
    _default_human_prompt: ty.ClassVar[PromptTemplate] =\
        _load_prompt_template('human.md')

    @classmethod
    def _check_prompt_template(
            cls,
            prompt_template: PromptTemplate | str | None,
            default: PromptTemplate
    ) -> PromptTemplate:
        if prompt_template is None:
            return default
        elif isinstance(prompt_template, PromptTemplate):
            return prompt_template
        else:
            return PromptTemplate.from_template(
                prompt_template, format='mustache')

    @classmethod
    def _make_llm(
            cls,
            llm: BaseChatModel | None,
            **kwargs: ty.Any
    ) -> BaseChatModel:
        if llm is not None:
            return llm
        else:
            provider = kwargs.pop('provider', 'ollama')
            if provider == 'ollama':
                from langchain_ollama import ChatOllama
                model = kwargs.pop('model', 'llama3.2')
                return ChatOllama(model=model, **kwargs)
            elif provider == 'openai':
                import getpass
                import os

                from langchain_openai import ChatOpenAI
                if 'OPENAI_API_KEY' not in os.environ:
                    os.environ['OPENAI_API_KEY'] = getpass.getpass(
                        'Enter your OpenAI API key: ')
                return ChatOpenAI(**kwargs)
            else:
                raise ValueError(f'bad provider: {provider}')

    #: The underlying language model.
    llm: BaseChatModel

    #: The system prompt.
    system_prompt: PromptTemplate

    #: The human prompt.
    human_prompt: PromptTemplate

    #: The messages to send to LLM.
    messages: list[BaseMessage] | None

    def __init__(
            self,
            machine: Tape | None = None,
            halt: Tape | None = None,
            work: Tape | None = None,
            state: Tape | None = None,
            symbol: Tape | None = None,
            left_symbol: Tape | None = None,
            next_state: Tape | None = None,
            next_symbol: Tape | None = None,
            next_move: Tape | None = None,
            subst1: Tape | None = None,
            subst2: Tape | None = None,
            steps: int | None = None,
            _empty: bool | None = None,
            system_prompt: PromptTemplate | str | None = None,
            human_prompt: PromptTemplate | str | None = None,
            llm: BaseChatModel | None = None,
            **kwargs: ty.Any
    ) -> None:
        super().__init__(
            machine,
            halt,
            work,
            state,
            symbol,
            left_symbol,
            next_state,
            next_symbol,
            next_move,
            subst1,
            subst2,
            steps,
            _empty)
        self.llm = self._make_llm(llm, **kwargs)
        self.system_prompt = self._check_prompt_template(
            system_prompt, self._default_system_prompt)
        self.human_prompt = self._check_prompt_template(
            human_prompt, self._default_human_prompt)
        self.messages = None   # initialized at the first step

    _re_step6_work: ty.Final[re.Pattern[str]] = re.compile(
        r'<work>(.*?)</work>', re.IGNORECASE)

    @ty.override
    def step6(self) -> ty.Self:
        if self.messages is None:
            self.messages = [
                SystemMessage(content=self.system_prompt.format()),
                HumanMessage(content=self.human_prompt.format(
                    machine=' '.join(map(''.join, self._parse_machine())),
                    work=''.join(self._parse_work())))]
            _logger.info('sending to LLM:\n%s', self.messages[0].content)
        else:
            self.messages.append(HumanMessage('continue'))
        assert self.messages is not None
        saved_work = self.work
        super().step6()
        _logger.info('sending to LLM:\n%s', self.messages[-1].content)
        response = self.llm.invoke(self.messages)
        assert isinstance(response.content, str)
        _logger.info('received from LLM:\n%s', response.content)
        m = self._re_step6_work.search(response.content)
        if m is None:
            raise self.Error('bad work: failed parse LLM response')
        work = self.check_tape(m.group(1), pad=True)
        if self.work != work:
            raise self.Error(f'''\
bad work:
- before step6:               {saved_work}
- after step6, expected:      {self.work}
- after step6, got from LLM:  {work}''')
        self.messages.append(response)
        return self
