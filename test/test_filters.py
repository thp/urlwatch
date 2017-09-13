from urlwatch.filters import GetElementById
from urlwatch.filters import GetElementByTag

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
