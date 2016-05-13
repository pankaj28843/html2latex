# -*- coding: utf-8 -*-

from lxml import etree


def get_columns_count(html):
    _root = etree.HTML(html)
    max_td_count = 0

    for row in _root.findall('.//tr'):
        col_count = 0

        cells = row.findall('.//td') + row.findall('.//th')

        for td in cells:
            colspan = td.attrib.get('colspan')
            if colspan:
                col_count += int(str(colspan))
            else:
                col_count += 1

        if col_count > max_td_count:
            max_td_count = col_count
    return max_td_count


def get_rows_count(html):
    _root = etree.HTML(html)
    return len(_root.findall('.//tr'))


def get_blank_tr():
    return etree.HTML('<tr>\n</tr>').find('.//tr')


def get_blank_td():
    td = etree.HTML('<td>\n</td>').find('.//td')
    td.set('__bottom_line', '1')
    return td


def create_blank_table(rows, cols):
    blank_html = '''
    <table  border="1">
    <tbody></tbody>
    </table>
    '''
    _root = etree.HTML(blank_html)
    _table = _root.find('.//table')
    _tbody = _table.find('.//tbody')

    for _i in range(rows):
        _tr = get_blank_tr()
        _tbody.insert(_i, _tr)

        for _j in range(cols):
            _td = get_blank_td()
            _tr.insert(_j, _td)

    return _root.find('.//table')


def find_next_untouched_td(_tr, col_index):
    for _td in _tr.findall('.//td')[col_index:]:
        if _td.attrib.get('__is_used') is None:
            return _td


def replace_td(_tr, old_td, new_td):
    _col_index = _tr.index(old_td)
    _tr.insert(_col_index, new_td)
    _tr.remove(old_td)
    new_td.set('__is_used', '1')


def unpack_merged_cells_in_table(html):
    rows_count = get_rows_count(html)
    columns_count = get_columns_count(html)
    new_table = create_blank_table(rows_count, columns_count)

    root = etree.HTML(html)

    for _tbody in root.findall('.//tbody') + root.findall('.//thead'):
        _tbody.tag = 'tbody'

    for _td in root.findall('.//td') + root.findall('.//th'):
        _td.set('__bottom_line', '1')
        _td.tag = 'td'

        try:
            _td.attrib.pop('__is_used')
        except KeyError:
            pass

        colspan = int(_td.attrib.get('colspan', 1))
        rowspan = int(_td.attrib.get('rowspan', 1))

        if colspan == 1:
            try:
                _td.attrib.pop('colspan')
            except KeyError:
                pass

        if rowspan == 1:
            try:
                _td.attrib.pop('rowspan')
            except KeyError:
                pass

    root = etree.HTML(etree.tounicode(root))

    for row_index, tr in enumerate(root.findall('.//tr')):
        new_tr = new_table.findall('.//tr')[row_index]

        for k, v in tr.attrib.items():
            new_tr.set(k, v)

        all_cells = []

        for td in tr.iterchildren():
            colspan = int(td.attrib.get('colspan', 1))
            all_cells.append(td)

            for _ in range(1, colspan):
                all_cells.append(None)

        col_index = 0
        for td in tr.iterchildren():
            colspan = int(td.attrib.get('colspan', 1))
            rowspan = int(td.attrib.get('rowspan', 1))

            if colspan == 1 and rowspan == 1:
                td_to_be_removed = find_next_untouched_td(new_tr, col_index)
                replace_td(new_tr, td_to_be_removed, td)

                col_index += 1
            if colspan > 1:
                col_index = all_cells.index(td)
                colspan = int(td.attrib.get('colspan'))
                td_to_be_removed = find_next_untouched_td(new_tr, col_index)
                replace_td(new_tr, td_to_be_removed, td)

                td.attrib.pop('colspan')
                td.set('_colspan', str(colspan))

                for _col_index in range(col_index + 1, col_index + colspan):
                    _td = new_tr.findall('.//td')[_col_index]

                    _td.set('__is_used', '1')

                # set next col_index
                col_index = _col_index + 1
            elif rowspan > 1:
                td_to_be_removed = find_next_untouched_td(new_tr, col_index)
                replace_td(new_tr, td_to_be_removed, td)

                td.attrib.pop('rowspan')
                td.set('_rowspan', str(rowspan))

                try:
                    td.attrib.pop('__bottom_line')
                except KeyError:
                    pass

                for _row_index in range(row_index + 1, row_index + rowspan):
                    _tr = new_table.findall('.//tr')[_row_index]
                    _td = _tr.findall('.//td')[col_index]
                    _td.set('__is_used', '1')

                    try:
                        _td.attrib.pop('__bottom_line')
                    except KeyError:
                        pass

                _td.set('__bottom_line', '1')

                col_index += 1

    for _td in new_table.findall('.//td') + new_table.findall('.//th'):
        try:
            _td.attrib.pop('__is_used')
        except KeyError:
            pass

    return etree.tounicode(new_table)

if __name__ == '__main__':
    html = r'''

<table border="0" cellpadding="0" cellspacing="0" style="width:580px">
    <tbody>
        <tr>
            <td rowspan="2" style="height:51px; width:60px">Tick One</td>
            <td rowspan="2" style="width:76px">Terms (Yrs)</td>
            <td rowspan="2" style="width:80px">No. of Issue</td>
            <td colspan="2" style="width:101px">Cover prices</td>
            <td colspan="2" style="width:101px">You pay</td>
            <td colspan="2" style="width:101px">You save</td>
            <td rowspan="2" style="width:60px">% saving</td>
        </tr>
        <tr>
            <td style="height:20px">USD</td>
            <td>Rs.</td>
            <td>USD</td>
            <td>Rs.</td>
            <td>USD</td>
            <td>Rs.</td>
        </tr>
        <tr>
            <td style="height:20px">&nbsp;</td>
            <td>1</td>
            <td>12</td>
            <td>120</td>
            <td>480</td>
            <td>102</td>
            <td>400</td>
            <td>18</td>
            <td>80</td>
            <td>17</td>
        </tr>
        <tr>
            <td style="height:20px">&nbsp;</td>
            <td>2</td>
            <td>24</td>
            <td>240</td>
            <td>960</td>
            <td>192</td>
            <td>750</td>
            <td>48</td>
            <td>210</td>
            <td>22</td>
        </tr>
        <tr>
            <td style="height:20px">&nbsp;</td>
            <td>3</td>
            <td>36</td>
            <td>360</td>
            <td>1440</td>
            <td>252</td>
            <td>1000</td>
            <td>108</td>
            <td>440</td>
            <td>30</td>
        </tr>
    </tbody>
</table>    '''

    output_html = unpack_merged_cells_in_table(html)
    import os
    import lxml
    output_html = etree.tostring(lxml.html.document_fromstring(output_html)[0])
    print output_html

    with open(os.path.expanduser('~/unmerged_table.html'), 'w') as f:
        f.write(output_html)
