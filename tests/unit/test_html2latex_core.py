from html2latex.html2latex import html2latex
from tests.fixtures.harness import get_fixture_case, normalize_fixture_text


def test_html2latex_empty_fragment_returns_empty():
    assert html2latex("   ") == ""


def test_html2latex_math_tex_span():
    fixture = get_fixture_case("inline/math/span-tex")
    output = html2latex(fixture.html)
    assert normalize_fixture_text(output) == normalize_fixture_text(fixture.tex)


def test_html2latex_anchor_without_href():
    fixture = get_fixture_case("inline/link/no-href")
    output = html2latex(fixture.html)
    assert normalize_fixture_text(output) == normalize_fixture_text(fixture.tex)


def test_html2latex_anchor_with_href():
    fixture = get_fixture_case("inline/link/basic")
    output = html2latex(fixture.html)
    assert normalize_fixture_text(output) == normalize_fixture_text(fixture.tex)


def test_html2latex_comment_skipped():
    fixture = get_fixture_case("blocks/paragraph/comment-between")
    output = html2latex(fixture.html)
    assert "note" not in output
    assert "Hi" in output
    assert "Bye" in output


def test_html2latex_list_items_have_spacing():
    fixture = get_fixture_case("lists/unordered/basic")
    output = html2latex(fixture.html)
    assert "\\item One" in output
    assert "\\item Two" in output


def test_html2latex_table_headers_and_colspan():
    fixture = get_fixture_case("blocks/table/headers-colspan")
    output = html2latex(fixture.html)
    assert "\\textbf{H1}" in output
    assert "\\textbf{H2}" in output
    assert "\\multicolumn{2}{l}{Body}" in output
