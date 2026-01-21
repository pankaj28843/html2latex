from __future__ import annotations


def capfirst(value: str | None) -> str | None:
    return value and value[0].upper() + value[1:]


def get_width_of_element_by_xpath(browser, xpath: str):
    javascript_code = (
        """
    document.evaluate('{xpath}', document, null,\
        XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.offsetWidth;
    """.format(xpath=xpath)
        .strip()
    )
    return browser.evaluate_script(javascript_code)

