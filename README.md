[![Build Status](https://travis-ci.org/thp/urlwatch.svg)](https://travis-ci.org/thp/urlwatch)

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
  * [appdirs](https://github.com/ActiveState/appdirs)
  * [chump](https://github.com/karanlyons/chump/) (for Pushover support)
  * [pushbullet.py](https://github.com/randomchars/pushbullet.py) (for Pushbullet support)

The dependencies can be installed with (add `--user` to install to `$HOME`):

`python3 -m pip install pyyaml minidb requests keyring appdirs`

For optional pushover support the chump package is required:

`python3 -m pip install chump`

For optional pushbullet support the pushbullet.py package is required:

`python3 -m pip install pushbullet.py`

For optional support for the "browser" job kind, Requests-HTML is needed:

`python3 -m pip install requests-html`

For unit tests, you also need to install pycodestyle:

`python3 -m pip install pycodestyle`


MIGRATION FROM URLWATCH 1.x
---------------------------

Migration from urlwatch 1.x should be automatic on first start. Here is a
quick rundown of changes in 2.0:

 * URLs are stored in a YAML file now, with direct support for specifying
   names for jobs, different job kinds, directly applying filters, selecting
   the HTTP request method, specifying POST data as dictionary and much more
 * The cache directory has been replaced with a SQLite 3 database file
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
url: https://thp.io/2008/urlwatch/
filter: html2text,grep:Current.*version,strip
```
For most cases, this means that you can specify a filter chain in
your urls.yaml page without requiring a custom hook where previously
you would have needed to write custom filtering code in Python.

If you want to extract only the body tag you can use this filer:
```yaml
url: https://thp.io/2008/urlwatch/
filter: element-by-tag:body
```

You can also specify an external `diff`-style tool (a tool that takes
two filenames (old, new) as parameter and returns on its standard output
the difference of the files), for example to use GNU `wdiff` to get
word-based differences instead of line-based difference:

```
url: https://example.com/
diff_tool: wdiff
```

Note that `diff_tool` specifies an external command-line tool, so that
tool must be installed separately (e.g. `apt install wdiff` on Debian or
`brew install wdiff` on macOS). Coloring is supported for `wdiff`-style
output, but potentially not for other diff tools.

PUSHOVER
--------

You can configure urlwatch to send real time notifications about changes
via Pushover(https://pushover.net/). To enable this, ensure you have the
chump python package installed (see DEPENDENCIES). Then edit your config
(`urlwatch --edit-config`) and enable pushover. You will also need to add
to the config your Pushover user key and a unique app key (generated by
registering urlwatch as an application on your Pushover account(https://pushover.net/apps/build)


PUSHBULLET
--------

Pushbullet notification are configured similarly to Pushover (see above).
You'll need to add to the config your Pushbullet Access Token, which you 
can generate at https://www.pushbullet.com/#settings

TELEGRAM
--------

Telegram notifications are configured using the Telegram Bot API.
For this, you'll need a Bot API token and a chat id (see https://core.telegram.org/bots).
Sample configuration:
```yaml
telegram:
  bot_token: '999999999:3tOhy2CuZE0pTaCtszRfKpnagOG8IQbP5gf' # your bot api token
  chat_id: '88888888' # the chat id where the messages should be sent
  enabled: true
```

BROWSER
-------

If the webpage you are trying to watch runs client-side JavaScript to
render the page, [Requests-HTML](http://html.python-requests.org) can
now be used to render the page in a headless Chromium instance first
and then use the HTML of the resulting page.

Use the `browser` kind in the configuration and the `navigate` key to set the
URL to retrieve. note that the normal `url` job keys are not supported
for the `browser` job types at the moment, for example:

```yaml
kind: browser
name: "A Page With JavaScript"
navigate: http://example.org/
```


E-MAIL VIA GMAIL SMTP
---------------------

You need to configure your GMail account to allow for "less secure" (password-based)
apps to login:

1. Go to https://myaccount.google.com/
2. Click on "Sign-in & security"
3. Scroll all the way down to "Allow less secure apps" and enable it

Now, start the configuration editor: `urlwatch --edit-config`

These are the keys you need to configure (see #158):

- `report/email/enabled`: `true`
- `report/email/from`: `your.username@gmail.com` (edit accordingly)
- `report/email/method`: `smtp`
- `report/email/smtp/host`: `smtp.gmail.com`
- `report/email/smtp/keyring`: `true`
- `report/email/smtp/port`: `587`
- `report/email/smtp/starttls`: `true`
- `report/email/to`: The e-mail address you want to send reports to

Now, for setting the password, it's not stored in the config file, but in your
keychain. To store the password, run: `urlwatch --smtp-login` and enter your
password.


TESTING FILTERS
---------------

While creating your filter pipeline, you might want to preview what the filtered
output looks like. You can do so by first configuring your job and then running
urlwatch with the `--test-filter` command, passing in the index (from `--list`)
or the URL/location of the job to be tested:

```
urlwatch --test-filter 1   # Test the first job in the list
urlwatch --test-filter https://example.net/  # Test the job with the given URL
```

The output of this command will be the filtered plaintext of the job, this is the
output that will (in a real urlwatch run) be the input to the diff algorithm.


CONTACT
-------

Website: https://thp.io/2008/urlwatch/

E-Mail: m@thp.io
