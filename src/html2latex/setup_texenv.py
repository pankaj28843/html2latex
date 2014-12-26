# Third Party Stuff
import jinja2

from .utils.text import escape_tex


def setup_texenv(loader):
    texenv = jinja2.Environment(loader=loader)
    texenv.block_start_string = '((*'
    texenv.block_end_string = '*))'
    texenv.variable_start_string = '((('
    texenv.variable_end_string = ')))'
    texenv.comment_start_string = '((='
    texenv.comment_end_string = '=))'
    texenv.filters['escape_tex'] = escape_tex

    return texenv
