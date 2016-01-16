"""A tool for monitoring webpages for updates

urlwatch is intended to help you watch changes in webpages and get notified
(via email, in your terminal or with a custom-written reporter class) of any
changes. The change notification will include the URL that has changed and
a unified diff of what has changed.
"""

pkgname = 'urlwatch'

__copyright__ = 'Copyright 2008-2016 Thomas Perl'
__author__ = 'Thomas Perl <m@thp.io>'
__license__ = 'BSD'
__url__ = 'http://thp.io/2008/urlwatch/'
__version__ = '2.0'
__user_agent__ = '%s/%s (+http://thp.io/2008/urlwatch/info.html)' % (pkgname, __version__)
