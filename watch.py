#!/usr/bin/python
# Minimalistic Python URL watcher
# 2008-03-04 Thomas Perl <thpinfo.com>
# http://thpinfo.com/2008/urlwatch

# 1. Create an "urls.txt" file and add one URL per
#    line that you want to watch.
# 2. Add watch.py as a cronjob or run it manually.
# 3. If something changed, you'll get a diff output
#    to stdout. If nothing changed, no output.
# 4. If you want to filter the web pages, because
#    there is some dynamic content that _always_
#    changes, create a "hooks.py" file that has a
#    filter(url, data) -> filtered_data function

# Configuration section
display_errors = False

# Code section

import sha
import sys
import os.path
import urllib2
import difflib

os.chdir(os.path.dirname(sys.argv[0]))

if os.path.exists('hooks.py'):
    from hooks import filter
else:
    filter = lambda x, y: y

for url in (x for x in open('urls.txt').read().splitlines() if not (x.startswith('#') or x.strip()=='')):
    filename = sha.new(url).hexdigest()
    try:
        data = filter(url, urllib2.urlopen(url).read())
        if os.path.exists(filename):
            old_data = open(filename).read()
            diff = ''.join(difflib.unified_diff(old_data.splitlines(1), data.splitlines(1)))
            if len(diff) > 0:
                print '%s\nCHANGED: %s\n%s\n%s\n%s\n\n' % ('*'*60, url, '*'*60, diff, '*'*60)
        else:
            print '%s\nNEW: %s\n%s\n\n' % ('*'*60, url, '*'*60)
        open(filename, 'w').write(data)
    except urllib2.HTTPError, error:
        if display_errors:
            print '%s\nERROR: %s\n%s\n%s\n%s\n\n' % ('*'*60, url, '*'*60, error, '*'*60)
    except urllib2.URLError, error:
        if display_errors:
            print '%s\nERROR: %s\n%s\n%s\n%s\n\n' % ('*'*60, url, '*'*60, error, '*'*60)

