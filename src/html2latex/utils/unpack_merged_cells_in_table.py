# -*- coding: utf-8 -*-

from justhtml import JustHTML
from justhtml.node import Element


def _parse_fragment(html):
    return JustHTML(html, fragment=True, safe=False).root


def _element_children(node):
    return [child for child in getattr(node, "children", []) if isinstance(child, Element)]


def _find_all(node, tag):
    matches = []
    for child in getattr(node, "children", []):
        if isinstance(child, Element):
            if child.name == tag:
                matches.append(child)
            matches.extend(_find_all(child, tag))
    return matches


def get_columns_count(html):
    root = _parse_fragment(html)
    max_td_count = 0

    for row in _find_all(root, "tr"):
        col_count = 0
        cells = [c for c in _element_children(row) if c.name in {"td", "th"}]

        for td in cells:
            colspan = td.attrs.get("colspan")
            if colspan:
                col_count += int(str(colspan))
            else:
                col_count += 1

        if col_count > max_td_count:
            max_td_count = col_count
    return max_td_count


def get_rows_count(html):
    root = _parse_fragment(html)
    return len(_find_all(root, "tr"))


def get_blank_tr():
    return Element("tr", {}, None)


def get_blank_td():
    td = Element("td", {}, None)
    td.attrs["__bottom_line"] = "1"
    return td


def create_blank_table(rows, cols):
    table = Element("table", {}, None)
    tbody = Element("tbody", {}, None)
    table.append_child(tbody)

    for _i in range(rows):
        tr = get_blank_tr()
        tbody.append_child(tr)
        for _j in range(cols):
            tr.append_child(get_blank_td())

    return table


def find_next_untouched_td(tr, col_index):
    tds = [c for c in _element_children(tr) if c.name == "td"]
    for td in tds[col_index:]:
        if td.attrs.get("__is_used") is None:
            return td
    return None


def replace_td(tr, old_td, new_td):
    children = _element_children(tr)
    try:
        idx = children.index(old_td)
    except ValueError:
        idx = len(children)
    tr.remove_child(old_td)
    ref = _element_children(tr)[idx] if idx < len(_element_children(tr)) else None
    tr.insert_before(new_td, ref)
    new_td.attrs["__is_used"] = "1"


def unpack_merged_cells_in_table(html):
    rows_count = get_rows_count(html)
    columns_count = get_columns_count(html)
    new_table = create_blank_table(rows_count, columns_count)

    root = _parse_fragment(html)

    for tbody in _find_all(root, "tbody") + _find_all(root, "thead"):
        tbody.name = "tbody"

    for td in _find_all(root, "td") + _find_all(root, "th"):
        td.name = "td"
        td.attrs["__bottom_line"] = "1"
        td.attrs.pop("__is_used", None)

    rows = _find_all(root, "tr")
    new_rows = _find_all(new_table, "tr")

    for row_index, tr in enumerate(rows):
        new_tr = new_rows[row_index]
        new_tr.attrs.update(tr.attrs)

        all_cells = [c for c in _element_children(tr) if c.name == "td"]

        col_index = 0
        for td in all_cells:
            if td.attrs.get("colspan") is None and td.attrs.get("rowspan") is None:
                td_to_be_removed = find_next_untouched_td(new_tr, col_index)
                if td_to_be_removed is None:
                    continue
                replace_td(new_tr, td_to_be_removed, td)
                col_index += 1
                continue

            if td.attrs.get("colspan"):
                col_index = all_cells.index(td)
                colspan = int(td.attrs.get("colspan"))
                td_to_be_removed = find_next_untouched_td(new_tr, col_index)
                if td_to_be_removed is None:
                    continue
                replace_td(new_tr, td_to_be_removed, td)

                td.attrs.pop("colspan", None)
                td.attrs["_colspan"] = str(colspan)

                for _col_index in range(col_index + 1, col_index + colspan):
                    _td = _element_children(new_tr)[_col_index]
                    _td.attrs["__is_used"] = "1"

                col_index = _col_index + 1
                continue

            if td.attrs.get("rowspan"):
                rowspan = int(td.attrs.get("rowspan"))
                td_to_be_removed = find_next_untouched_td(new_tr, col_index)
                if td_to_be_removed is None:
                    continue
                replace_td(new_tr, td_to_be_removed, td)

                td.attrs.pop("rowspan", None)
                td.attrs["_rowspan"] = str(rowspan)
                td.attrs.pop("__bottom_line", None)

                for _row_index in range(row_index + 1, row_index + rowspan):
                    _tr = new_rows[_row_index]
                    _td = _element_children(_tr)[col_index]
                    _td.attrs["__is_used"] = "1"
                    _td.attrs.pop("__bottom_line", None)

                _td.attrs["__bottom_line"] = "1"
                col_index += 1

    for td in _find_all(new_table, "td"):
        td.attrs.pop("__is_used", None)

    return new_table.to_html(pretty=False)


if __name__ == "__main__":
    html = r"""
    <p><strong>Go to your nearest farmer and collect the information for the following table:</strong></p>

<table border="1" cellpadding="0" cellspacing="0" style="width:604px">
    <tbody>
        <tr>
            <td rowspan="2" style="height:41px; width:227px">
            <p style="text-align:center"><strong>Paddy growing season</strong></p>
            </td>
            <td rowspan="2" style="height:41px">
            <p style="text-align:center"><strong>Paddy production per hectare</strong></p>
            </td>
            <td colspan="2" style="height:41px">
            <p style="text-align:center"><strong>Quality of seed</strong></p>
            </td>
        </tr>
        <tr>
            <td style="height:28px; width:57px">
            <p style="text-align:center"><strong>Size</strong></p>
            </td>
            <td style="height:28px; width:95px">
            <p style="text-align:center"><strong>Weight</strong></p>
            </td>
        </tr>
        <tr>
            <td style="height:79px; width:227px">
            <p style="text-align:center">Rabi<br />
            Kharif</p>
            </td>
            <td style="height:79px">&nbsp;</td>
            <td style="height:79px">&nbsp;</td>
        </tr>
    </tbody>
</table>

<p>&nbsp;</p>

<p>Students&#39; activity.</p>
    """

    print(unpack_merged_cells_in_table(html))
