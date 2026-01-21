from __future__ import absolute_import

# Standard Library
import os
import re

# Third Party Stuff
import jinja2

REGEX_SN = re.compile(r"(?i)\s*(s\s*\.*\s*no\.*|s\s*\.*\s*n\.*)\s*")


def render_html(html):
    static_root = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "../static",
    )
    context = {
        "html": html,
        "STATIC_ROOT": static_root,
    }

    loader = jinja2.FileSystemLoader(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "../templates",
        )
    )
    jinja2_env = jinja2.Environment(loader=loader)
    template = jinja2_env.get_template("web2png.html")
    return template.render(**context)
