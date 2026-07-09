from urlwatch.util import chunkstring, should_ignore_http_code

import pytest

TESTDATA = [
    # Numbering for just one item doesn't add the numbers
    (('Hello World', 100, True, ['Hello World'])),
    (('This Is A Long Message', 5, False, ['This', 'Is A', 'Long', 'Messa', 'ge'])),
    (('This Is A Very Long Message That Should Be Numbered', 20, True,
     # 12345678901234567890
      ['This Is A Very (1/4)',
       'Long Message (2/4)',
       'That Should Be (3/4)',
       'Numbered (4/4)'])),
    (('Averylongwordthathas\nnewlineseparationgoingon', 15, True,
      # 123456789012345
      ['Averylong (1/6)',
       'wordthath (2/6)',
       'as (3/6)',
       'newlinese (4/6)',
       'parationg (5/6)',
       'oingon (6/6)'])),
]


@pytest.mark.parametrize('string, length, numbering, output', TESTDATA)
def test_chunkstring(string, length, numbering, output):
    assert list(chunkstring(string, length, numbering=numbering)) == output


@pytest.mark.parametrize('ignore_list, status_code, expected', [
    ('404', 404, True),
    ('404', 200, False),
    ('404', 500, False),
    ('4xx', 404, True),
    ('4xx', 403, True),
    ('4xx', 500, False),
    ('404,500', 404, True),
    ('404,500', 500, True),
    ('404,500', 403, False),
    ([404, 500], 404, True),
    ([404, 500], 500, True),
    ([404, 500], 403, False),
    (['404', '500'], 404, True),
    (['404', '500'], 403, False),
    (404, 404, True),
    (404, 403, False),
])
def test_should_ignore_http_code(ignore_list, status_code, expected):
    assert should_ignore_http_code(status_code, ignore_list) == expected
