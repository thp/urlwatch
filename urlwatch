#!/usr/bin/python
# urlwatch is a minimalistic URL watcher written in Python
# Started: 2008-03-04 Thomas Perl <thpinfo.com>

"""Watch web pages and arbitrary URLs for changes"""

__author__ = 'Thomas Perl <thpinfo.com>'
__copyright__ = 'Copyright 2008 Thomas Perl'
__license__ = 'BSD'
__homepage__ = 'http://thpinfo.com/2008/urlwatch/'
__version__ = 1.5

user_agent = 'urlwatch/%s (+http://thpinfo.com/2008/urlwatch/info.html)' % __version__


# Configuration section
display_errors = False
line_length = 75


# File and folder paths
import sys
import os.path

urlwatch_dir = os.path.expanduser(os.path.join('~', '.urlwatch'))
urls_txt = os.path.join(urlwatch_dir, 'urls.txt')
cache_dir = os.path.join(urlwatch_dir, 'cache')
scripts_dir = os.path.join(urlwatch_dir, 'lib')
hooks_py = os.path.join(scripts_dir, 'hooks.py')

# Check if we are installed in the system already
(prefix, bindir) = os.path.split(os.path.dirname(os.path.abspath(sys.argv[0])))

if bindir == 'bin':
    # Assume we are installed in system
    examples_dir = os.path.join(prefix, 'share', 'urlwatch', 'examples')
else:
    # Assume we are not yet installed
    examples_dir = os.path.join(prefix, bindir, 'examples')

urls_txt_example = os.path.join(examples_dir, 'urls.txt.example')

# Code section
import sha
import shutil
import os
import urllib2
import difflib
import datetime

def foutput(type, url, content=None, summary=None, c='*', n=line_length):
    """Format output messages
    
    Returns a snippet of a specific message type (i.e. 'changed') for
    a specific URL and an optional (possibly multi-line) content.

    The parameter "summary" (if specified) should be a list variable
    that gets one item appended for the summary of the changes.

    The return value is a list of strings (one item per line).
    """
    summary_txt = ': '.join((type.upper(), url))

    if summary is not None:
        if content is None:
            summary.append(summary_txt)
        else:
            summary.append('%s (%d bytes)' % (summary_txt, len(content)))

    result = [c*n, summary_txt]
    if content is not None:
        result += [c*n, content]
    result += [c*n, '', '']

    return result


if __name__ == '__main__':
    start = datetime.datetime.now()

    # Created all needed folders
    for needed_dir in (urlwatch_dir, cache_dir, scripts_dir):
        if not os.path.isdir(needed_dir):
            os.makedirs(needed_dir)

    # Check for required files
    if not os.path.isfile(urls_txt):
        example_fn = os.path.join(os.path.dirname(urls_txt), os.path.basename(urls_txt_example))
        print 'Error: You need to create a urls.txt file first.'
        print ''
        print 'Place it in %s' % (urls_txt)
        print 'An example is available in %s' % (example_fn)
        print ''
        if os.path.exists(urls_txt_example) and not os.path.exists(example_fn):
            shutil.copy(urls_txt_example, example_fn)
        sys.exit(1)

    headers = {
            'User-agent': user_agent,
    }

    summary = []
    details = []
    count = 0

    if os.path.exists(hooks_py):
        hooks = imp.load_source('hooks', hooks_py)
        if hasattr(hooks, 'filter'):
            filter = hooks.filter
        else:
            print 'WARNING: %s has no filter function - ignoring' % hooks_py
            filter = lambda x, y: y
    else:
        filter = lambda x, y: y

    for url in (x for x in open(urls_txt).read().splitlines() if not (x.startswith('#') or x.strip()=='')):
        filename = os.path.join(cache_dir, sha.new(url).hexdigest())
        try:
            request = urllib2.Request(url, None, headers)
            data = filter(url, urllib2.urlopen(request).read())
            if os.path.exists(filename):
                old_data = open(filename).read()
                diff = ''.join(difflib.unified_diff(old_data.splitlines(1), data.splitlines(1)))
                if len(diff) > 0:
                    details += foutput('changed', url, diff, summary)
            else:
                details += foutput('new', url, None, summary)
            open(filename, 'w').write(data)
        except urllib2.HTTPError, error:
            if display_errors:
                details += foutput('error', url, error, summary)
        except urllib2.URLError, error:
            if display_errors:
                details += foutput('error', url, error, summary)
        count += 1

    end = datetime.datetime.now()

    # Output everything
    if len(summary) > 1:
        print '-'*line_length
        print 'summary: %d changes' % (len(summary),)
        print ''
        for id, line in enumerate(summary):
            print '%02d. %s' % (id+1, line)
        print '-'*line_length
        print '\n\n\n'
    if len(details) > 1:
        print '\n'.join(details)
        print '-- '
        print 'urlwatch %s, %s' % (__version__, __copyright__)
        print 'Website: %s' % (__homepage__,)
        print 'watched %d URLs in %d seconds\n' % (count, (end-start).seconds)

