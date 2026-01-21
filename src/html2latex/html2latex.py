# -*- coding: utf-8 -*-
"""
Convert HTML generated from CKEditor to LaTeX environment.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys

from .elements import H1, H2, H3, H4, IMG, TD, TH, TR, A, HTMLElement, Table, delegate
from .helpers import capfirst, get_width_of_element_by_xpath
from .pipeline import _html2latex, fix_encoding_of_html_using_lxml, html2latex
from .template_env import get_texenv, loader, texenv
from .utils.spellchecker import check_spelling

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

VERSION = "0.0.63"
CAPFIRST_ENABLED = False

__all__ = [
    "A",
    "H1",
    "H2",
    "H3",
    "H4",
    "IMG",
    "TD",
    "TH",
    "TR",
    "Table",
    "HTMLElement",
    "_html2latex",
    "capfirst",
    "check_spelling",
    "delegate",
    "fix_encoding_of_html_using_lxml",
    "get_texenv",
    "get_width_of_element_by_xpath",
    "html2latex",
    "loader",
    "os",
    "subprocess",
    "texenv",
]
