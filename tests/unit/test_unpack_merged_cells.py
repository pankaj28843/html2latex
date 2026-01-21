from html2latex.html_adapter import parse_html
from html2latex.utils.unpack_merged_cells_in_table import (
    get_columns_count,
    get_rows_count,
    unpack_merged_cells_in_table,
)


def test_unpack_merged_cells_rowspan():
    html = (
        "<table><tbody><tr><td rowspan='2'>A</td><td>B</td></tr><tr><td>C</td></tr></tbody></table>"
    )

    assert get_rows_count(html) == 2
    assert get_columns_count(html) == 2

    output = unpack_merged_cells_in_table(html)
    root = parse_html(output).root
    rows = root.findall(".//tr")
    assert len(rows) == 2

    row1_cells = rows[0].findall(".//td")
    assert row1_cells[0].attrib.get("_rowspan") == "2"
    assert row1_cells[0].attrib.get("__bottom_line") is None


def test_unpack_merged_cells_colspan():
    html = "<table><tbody><tr><td colspan='2'>A</td></tr></tbody></table>"

    output = unpack_merged_cells_in_table(html)
    root = parse_html(output).root
    row = root.findall(".//tr")[0]
    cells = row.findall(".//td")
    assert cells[0].attrib.get("_colspan") == "2"
