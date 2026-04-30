# Copyright (C) 2026 PUC-Rio/PUC-Behring Institute for AI
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os

from .__version__ import __description__, __title__, __version__  # noqa: F401
from .um import UM

__all__ = (
    'UM',
)


def _reset_logging(
        debug: bool | None = bool(os.getenv('UMLLM_DEBUG')),
        info: bool | None = bool(os.getenv('UMLLM_INFO'))
) -> None:
    if debug or info:
        import logging
        logging.basicConfig()
        if debug:
            level = logging.DEBUG
        else:
            level = logging.INFO
        logging.getLogger().setLevel(level)


_reset_logging()
