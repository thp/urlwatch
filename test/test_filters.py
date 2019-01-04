from urlwatch.filters import GetElementById
from urlwatch.filters import GetElementByTag
from urlwatch.filters import JsonFormatFilter
from urlwatch.filters import XPathFilter
from urlwatch.filters import CssFilter

from nose.tools import eq_


def test_get_element_by_id():
    get_element_by_id = GetElementById(None, None)
    result = get_element_by_id.filter("""
    <html><head></head><body>
    <div id="foo">asdf <span>bar</span></div>
    <div id="bar">asdf <span>bar</span> hoho</div>
    </body></html>
    """, 'bar')
    print(result)
    eq_(result, '<div id="bar">asdf <span>bar</span> hoho</div>')


def test_get_element_by_tag():
    get_element_by_tag = GetElementByTag(None, None)
    result = get_element_by_tag.filter("""
    <html><head></head><body>foo</body></html>
    """, 'body')
    print(result)
    eq_(result, '<body>foo</body>')


def test_get_element_by_tag_nested():
    get_element_by_tag = GetElementByTag(None, None)
    result = get_element_by_tag.filter("""
    <html><head></head><body>
    <div>foo</div>
    <div>bar</div>
    </body></html>
    """, 'div')
    print(result)
    eq_(result, """<div>foo</div><div>bar</div>""")


def test_json_format_filter():
    json_format_filter = JsonFormatFilter(None, None)
    result = json_format_filter.filter(
        """{"field1": {"f1.1": "value"},"field2": "value"}""")
    print(result)
    eq_(result, """{
    "field1": {
        "f1.1": "value"
    },
    "field2": "value"
}""")


def test_json_format_filter_subfilter():
    json_format_filter = JsonFormatFilter(None, None)
    result = json_format_filter.filter(
        """{"field1": {"f1.1": "value"},"field2": "value"}""", "2")
    print(result)
    eq_(result, """{
  "field1": {
    "f1.1": "value"
  },
  "field2": "value"
}""")


def test_xpath_elements():
    xpath_filter = XPathFilter(None, None)
    result = xpath_filter.filter("""
    <html><head></head><body>
    abc
    <div>foo</div>
    lmn
    <span id="bar">bar</span>
    xyz
    </body></html>
    """, "//div | //*[@id='bar']")
    print(result)
    eq_(result, """<div>foo</div>

<span id="bar">bar</span>
""")


def test_xpath_text():
    xpath_filter = XPathFilter(None, None)
    result = xpath_filter.filter("""
    <html><head></head><body>
    abc
    <div>foo</div>
    lmn
    <span id="bar">bar</span>
    xyz
    </body></html>
    """, '//div/text() | //span/@id')
    print(result)
    eq_(result, """foo
bar""")


def test_css():
    css_filter = CssFilter(None, None)
    result = css_filter.filter("""
    <html><head></head><body>
    abc
    <div>foo</div>
    lmn
    <span id="bar">bar</span>
    xyz
    </body></html>
    """, 'div, span')
    print(result)
    eq_(result, """<div>foo</div>

<span id="bar">bar</span>
""")
