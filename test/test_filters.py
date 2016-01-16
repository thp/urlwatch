from urlwatch.filters import GetElementById

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
