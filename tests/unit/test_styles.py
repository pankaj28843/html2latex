from html2latex.styles import StyleConfig


def test_style_config_defaults():
    config = StyleConfig()
    assert config.paragraph.align == "justify"
    assert config.list.kind == "itemize"
    assert config.table.header_bold is True
    assert config.image.placement == "htbp"
    assert config.heading.levels[0] == "section"
