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


@pytest.mark.parametrize('input, output', TESTDATA, ids=[str(d[0]) for d in TESTDATA])
def test_normalize_filter_list(input, output):
    assert list(FilterBase.normalize_filter_list(input)) == output


with open(os.path.join(os.path.dirname(__file__), 'data/filter_tests.yaml'), 'r', encoding='utf8') as f:
    FILTER_TESTS = list(yaml.safe_load(f).items())


@pytest.mark.parametrize('test_name, test_data', FILTER_TESTS, ids=[d[0] for d in FILTER_TESTS])
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


def test_shellpipe_inherits_environment_but_does_not_modify_it():
    # https://github.com/thp/urlwatch/issues/541

    # Set a specific value to check it doesn't overwrite the current env
    os.environ['URLWATCH_JOB_NAME'] = 'should-not-be-overwritten'

    # See if the shellpipe process can use a variable from the outside
    os.environ['INHERITED_FROM'] = 'parent-process'
    filtercls = FilterBase.__subclasses__.get('shellpipe')
    result = filtercls(None, None).filter('input-string', {'command': 'echo "$INHERITED_FROM/$URLWATCH_JOB_NAME"'})
    # Check that the inherited value and the job name is set properly
    assert result == 'parent-process/\n'

    # Check that outside the variable wasn't overwritten by the filter
    assert os.environ['URLWATCH_JOB_NAME'] == 'should-not-be-overwritten'


def test_html2text_does_not_modify_subfilter():
    # The subfilter dict passed to Html2TextFilter should not be modified by
    # the filter() method.
    expected_subfilter = {'method': 're', 'extra_arg': 42}
    subfilter = expected_subfilter.copy()
    filtercls = FilterBase.__subclasses__.get('html2text')
    filtercls(None, None).filter('unused', subfilter)
    assert subfilter == expected_subfilter
