from urlwatch.util import chunkstring
from nose.tools import eq_


def test_chunkstring():
    testdata = [
        # Numbering for just one item doesn't add the numbers
        (('Hello World', 100, True), ['Hello World']),
        (('This Is A Long Message', 5, False), ['This', 'Is A', 'Long', 'Messa', 'ge']),
        (('This Is A Very Long Message That Should Be Numbered', 20, True),
         # 12345678901234567890
         ['This Is A Very (1/4)',
          'Long Message (2/4)',
          'That Should Be (3/4)',
          'Numbered (4/4)']),
        (('Averylongwordthathas\nnewlineseparationgoingon', 15, True),
         # 123456789012345
         ['Averylong (1/6)',
          'wordthath (2/6)',
          'as (3/6)',
          'newlinese (4/6)',
          'parationg (5/6)',
          'oingon (6/6)']),
    ]

    def check_expected(string, length, numbering, output):
        eq_(list(chunkstring(string, length, numbering=numbering)), output)

    for (string, length, numbering), output in testdata:
        yield check_expected, string, length, numbering, output
