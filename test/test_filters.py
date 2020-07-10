import os
import logging
import yaml
from urlwatch.filters import FilterBase
from nose.tools import eq_

logger = logging.getLogger(__name__)


def test_normalize_filter_list():
    testdata = [
        ('grep', [('grep', {})]),
        ('grep:foo', [('grep', {'re': 'foo'})]),
        ('a,b:x,c', [('a', {}), ('b', 'x'), ('c', {})]),
        ([{'grep': None}], [('grep', {})]),
        ([{'grep': {'re': 'bla'}}], [('grep', {'re': 'bla'})]),
        ('re.sub:.*', [('re.sub', {'pattern': '.*'})]),
        ([{'reverse': '\n\n'}], [('reverse', {'separator': '\n\n'})]),
        ('re.sub', [('re.sub', {})]),
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

    def check_expected(input, output):
        eq_(list(FilterBase.normalize_filter_list(input)), output)

    for input, output in testdata:
        yield check_expected, input, output


def test_filters():
    def check_filter(test_name):
        filter = filter_tests[test_name]['filter']
        data = filter_tests[test_name]['data']
        expected_result = filter_tests[test_name]['expected_result']

        result = data
        for filter_kind, subfilter in FilterBase.normalize_filter_list(filter):
            logger.info('filter kind: %s, subfilter: %s', filter_kind, subfilter)
            filtercls = FilterBase.__subclasses__.get(filter_kind)
            if filtercls is None:
                raise ValueError('Unknown filter kind: %s:%s' % (filter_kind, subfilter))
            result = filtercls(None, None).filter(result, subfilter)

        logger.debug('Expected result:\n%s', expected_result)
        logger.debug('Actual result:\n%s', result)
        eq_(result, expected_result)

    with open(os.path.join(os.path.dirname(__file__), 'data/filter_tests.yaml'), 'r', encoding='utf8') as fp:
        filter_tests = yaml.load(fp, Loader=yaml.SafeLoader)
    for test_name in filter_tests:
        yield check_filter, test_name
