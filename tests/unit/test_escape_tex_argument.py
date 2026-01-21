from html2latex.utils.text import escape_tex_argument


def test_escape_tex_argument_special_chars():
    value = "file_{name}%#&_~^\\path"
    escaped = escape_tex_argument(value)
    assert "\\{" in escaped
    assert "\\}" in escaped
    assert "\\%" in escaped
    assert "\\#" in escaped
    assert "\\_" in escaped
    assert "\\&" in escaped
    assert "\\~{}" in escaped
    assert "\\^{}" in escaped
    assert "\\textbackslash" in escaped
