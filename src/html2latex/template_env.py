from __future__ import annotations

import os

import jinja2

from .setup_texenv import setup_texenv

_TEMPLATE_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates")

loader = jinja2.FileSystemLoader(_TEMPLATE_ROOT)
texenv = setup_texenv(loader)

