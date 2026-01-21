"""HTML helpers that don't require external dependencies."""

from html import unescape
from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts = []

    def handle_data(self, data: str) -> None:
        if data:
            self.parts.append(data)


def check_if_html_has_text(html: str) -> bool:
    if not html:
        return False
    parser = _TextExtractor()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        # If parsing fails, fall back to a simple whitespace check.
        return bool(html.strip())
    text = unescape("".join(parser.parts)).replace("\xa0", " ")
    return bool(text.strip())
