```
                         _               _       _       ____
              _   _ _ __| |_      ____ _| |_ ___| |__   |___ \
             | | | | '__| \ \ /\ / / _` | __/ __| '_ \    __) |
             | |_| | |  | |\ V  V / (_| | || (__| | | |  / __/
              \__,_|_|  |_| \_/\_/ \__,_|\__\___|_| |_| |_____|

                 A tool for monitoring webpages for updates
```
urlwatch is intended to help you watch changes in webpages and get notified
(via email, in your terminal or with a custom-written reporter class) of any
changes. The change notification will include the URL that has changed and
a unified diff of what has changed.


DEPENDENCIES
------------

urlwatch 2 requires:

  * Python 3.3 or newer
  * [PyYAML](http://pyyaml.org/)
  * [minidb](https://thp.io/2010/minidb/)
  * [requests](http://python-requests.org/)
  * [keyring](https://github.com/jaraco/keyring/)

The dependencies can be installed with (add `--user` to install to `$HOME`):

`python3 -m pip install pyyaml minidb requests keyring`


MIGRATION FROM URLWATCH 1.x
---------------------------

Migration from urlwatch 1.x should be automatic on first start. Here is a
quick rundown of changes in 2.0:

 * URLs are stored in a YAML file now, with direct support for specifying
   names for jobs, different job kinds, directly applying filters, selecting
   the HTTP request method, specifying POST data as dictionary and much more
 * The cache directory has been replaced with with a SQLite 3 database file
   "cache.db" in minidb format, storing all change history (use `--gc-cache` to
   remove old changes if you don't need them anymore) for further analysis
 * The hooks mechanism has been replaced with support for creating new job
   kinds by subclassing, new filters (also by subclassing) as well as new
   reporters (pieces of code that put the results somewhere, for example the
   default installation contains the "stdout" reporter that writes to the
   console and the "email" reporter that can send HTML and text e-mails)
 * A configuration file - urlwatch.yaml - has been added for specifying user
   preferences instead of having to supply everything via the command line


QUICK START
-----------

 1. Start `urlwatch` to migrate your old data or start fresh
 2. Use `urlwatch --edit` to customize your job list
 3. Use `urlwatch --edit-config` if you want to set up e-mail sending
 4. Use `urlwatch --edit-hooks` if you want to write custom subclasses
 5. Add `urlwatch` to your crontab (`crontab -e`)


TIPS AND TRICKS
---------------

Quickly adding new URLs to the job list from the command line:

```urlwatch --add url=http://example.org,name=Example```

You can pick only a given HTML element with the built-in filter, for
example to extract ```<div id="something">.../<div>``` from a page, you
can use the following in your urls.yaml:
```yaml
url: http://example.org/
filter: element-by-id:something
```

Also, you can chain filters, so you can run html2text on the result:
```yaml
url: http://example.net/
filter: element-by-id:something,html2text
```

The example urls.yaml file also demonstrates the use of built-in
filters, here 3 filters are used: html2text, line-grep and whitespace
removal to get just a certain info field from a webpage:
```yaml
url: http://thp.io/2008/urlwatch/
filter: html2text,grep:Current.*version,strip
```
For most cases, this means that you can specify a filter chain in
your urls.yaml page without requiring a custom hook where previously
you would have needed to write custom filtering code in Python.


CONTACT
-------

Website: http://thp.io/2008/urlwatch/

E-Mail: m@thp.io
