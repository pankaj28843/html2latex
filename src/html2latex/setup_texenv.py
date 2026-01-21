# Third Party Stuff
import jinja2

from .utils.text import escape_tex


def setup_texenv(loader):
    texenv = jinja2.Environment(
        loader=loader,
        autoescape=False,
        block_start_string="((*",
        block_end_string="*))",
        variable_start_string="(((",
        variable_end_string=")))",
        comment_start_string="((=",
        comment_end_string="=))",
        trim_blocks=False,
        lstrip_blocks=False,
        keep_trailing_newline=False,
    )
    texenv.filters["escape_tex"] = escape_tex

    return texenv
