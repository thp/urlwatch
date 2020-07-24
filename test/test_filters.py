import os
import logging
import yaml
from urlwatch.filters import FilterBase

import pytest

logger = logging.getLogger(__name__)

TESTDATA = [
    # Legacy string-style filter definition conversion
    ('grep', [('grep', {})]),
    ('grep:foo', [('grep', {'re': 'foo'})]),
    ('beautify,grep:foo,html2text', [('beautify', {}), ('grep', {'re': 'foo'}), ('html2text', {})]),
    ('re.sub:.*', [('re.sub', {'pattern': '.*'})]),
    ('re.sub', [('re.sub', {})]),

    # New dict-style filter definition normalization/mapping
    ([{'grep': None}], [('grep', {})]),
    ([{'grep': {'re': 'bla'}}], [('grep', {'re': 'bla'})]),
    ([{'reverse': '\n\n'}], [('reverse', {'separator': '\n\n'})]),
    (['html2text', {'grep': 'Current.*version'}, 'strip'], [
        ('html2text', {}),
        ('grep', {'re': 'Current.*version'}),
        ('strip', {}),
    ]),
    ([{'css': 'body'}], [('css', {'selector': 'body'})]),
    ([{'html2text': {'method': 'bs4', 'parser': 'html5lib'}}], [
        ('html2text', {'method': 'bs4', 'parser': 'html5lib'}),
    ]),
]


@pytest.mark.parametrize('input, output', TESTDATA)
def test_normalize_filter_list(input, output):
    assert list(FilterBase.normalize_filter_list(input)) == output


FILTER_TESTS = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), 'data/filter_tests.yaml'), 'r', encoding='utf8'))


@pytest.mark.parametrize('test_name, test_data', FILTER_TESTS.items())
def test_filters(test_name, test_data):
    filter = test_data['filter']
    data = test_data['data']
    expected_result = test_data['expected_result']

    result = data
    for filter_kind, subfilter in FilterBase.normalize_filter_list(filter):
        logger.info('filter kind: %s, subfilter: %s', filter_kind, subfilter)
        filtercls = FilterBase.__subclasses__.get(filter_kind)
        if filtercls is None:
            raise ValueError('Unknown filter kind: %s:%s' % (filter_kind, subfilter))
        result = filtercls(None, None).filter(result, subfilter)

    logger.debug('Expected result:\n%s', expected_result)
    logger.debug('Actual result:\n%s', result)
    assert result == expected_result


def test_invalid_filter_name_raises_valueerror():
    with pytest.raises(ValueError):
        list(FilterBase.normalize_filter_list(['afilternamethatdoesnotexist']))


def test_providing_subfilter_to_filter_without_subfilter_raises_valueerror():
    with pytest.raises(ValueError):
        list(FilterBase.normalize_filter_list([{'beautify': {'asubfilterthatdoesnotexist': True}}]))


def test_providing_unknown_subfilter_raises_valueerror():
    with pytest.raises(ValueError):
        list(FilterBase.normalize_filter_list([{'grep': {'re': 'Price: .*', 'anothersubfilter': '42'}}]))
