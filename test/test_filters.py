import os
import logging
import yaml
from urlwatch.filters import FilterBase
from nose.tools import eq_

from util import TEST_DATA_DIR

logger = logging.getLogger(__name__)


def test_filters():
    def check_filter(test_name):
        filter = filter_tests[test_name]['filter']
        data = filter_tests[test_name]['data']
        expected_result = filter_tests[test_name]['expected_result']
        if isinstance(filter, dict):
            key = next(iter(filter))
            kind, subfilter = key, filter[key]
        elif isinstance(filter, str):
            if ',' in filter:
                raise ValueError('Only single filter allowed in this test')
            elif ':' in filter:
                kind, subfilter = filter.split(':', 1)
            else:
                kind = filter
                subfilter = None
        logger.info('filter kind: %s, subfilter: %s', kind, subfilter)
        filtercls = FilterBase.__subclasses__.get(kind)
        if filtercls is None:
            raise ValueError('Unknown filter kind: %s:%s' % (filter_kind, subfilter))
        result = filtercls(None, None).filter(data, subfilter)
        logger.debug('Expected result:\n%s', expected_result)
        logger.debug('Actual result:\n%s', result)
        eq_(result, expected_result)

    with open(os.path.join(TEST_DATA_DIR, 'filter_tests.yaml'), 'r', encoding='utf8') as fp:
        filter_tests = yaml.load(fp)
    for test_name in filter_tests:
        yield check_filter, test_name
