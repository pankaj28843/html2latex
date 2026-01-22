from __future__ import annotations

import os
from contextvars import ContextVar

import jinja2

from .setup_texenv import setup_texenv

_TEMPLATE_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates")

loader = jinja2.FileSystemLoader(_TEMPLATE_ROOT)
_TEXENV: ContextVar[jinja2.Environment | None] = ContextVar("html2latex_texenv", default=None)


def get_texenv() -> jinja2.Environment:
    env = _TEXENV.get()
    if env is None:
        env = setup_texenv(loader)
        _TEXENV.set(env)
    return env


texenv = get_texenv()
