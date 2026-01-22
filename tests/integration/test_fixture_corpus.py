from html2latex.html2latex import html2latex
from tests.fixtures.harness import normalize_fixture_text


def test_fixture_case(fixture_case):
    if fixture_case.case_id.startswith("errors/"):
        return
    result = html2latex(fixture_case.html)
    assert normalize_fixture_text(result) == normalize_fixture_text(fixture_case.tex)
