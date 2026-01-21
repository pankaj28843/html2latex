from html2latex.html2latex import HTMLElement, capfirst, get_width_of_element_by_xpath
from html2latex.html_adapter import parse_html


class DummyBrowser:
    def __init__(self):
        self.last_script = None

    def evaluate_script(self, script):
        self.last_script = script
        return 128


def test_get_width_of_element_by_xpath():
    browser = DummyBrowser()
    width = get_width_of_element_by_xpath(browser, "//div")
    assert width == 128
    assert "//div" in browser.last_script


def test_remove_empty_noop():
    element = parse_html("<p>Hi</p>").root.find(".//p")
    html_element = HTMLElement(element)
    html_element.remove_empty()


def test_capfirst():
    assert capfirst("hello") == "Hello"
    assert capfirst("") == ""


def test_fix_tail_spacing():
    element = parse_html("<div><span>Hi</span> tail</div>").root.find(".//span")
    html_element = HTMLElement(element)
    assert html_element.content["tail"].startswith(" ")
