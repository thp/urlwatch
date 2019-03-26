[![Build Status](https://travis-ci.org/thp/urlwatch.svg)](https://travis-ci.org/thp/urlwatch)
[![Packaging status](https://repology.org/badge/tiny-repos/urlwatch.svg)](https://repology.org/metapackage/urlwatch/versions)
[![PyPI version](https://badge.fury.io/py/urlwatch.svg)](https://badge.fury.io/py/urlwatch)


```
                         _               _       _       ____
              _   _ _ __| |_      ____ _| |_ ___| |__   |___ \
             | | | | '__| \ \ /\ / / _` | __/ __| '_ \    __) |
             | |_| | |  | |\ V  V / (_| | || (__| | | |  / __/
              \__,_|_|  |_| \_/\_/ \__,_|\__\___|_| |_| |_____|

                                  ... monitors webpages for you
```
urlwatch is intended to help you watch changes in webpages and get notified
(via e-mail, in your terminal or through various third party services) of any
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
  * [lxml](https://lxml.de)
  * [cssselect](https://cssselect.readthedocs.io)
  * [enum34](https://pypi.org/project/enum34/) (Python 3.3 only)

The dependencies can be installed with (add `--user` to install to `$HOME`):

`python3 -m pip install pyyaml minidb requests keyring appdirs lxml cssselect`


Optional dependencies (install via `python3 -m pip install <packagename>`):

  * Pushover reporter: [chump](https://github.com/karanlyons/chump/)
  * Pushbullet reporter: [pushbullet.py](https://github.com/randomchars/pushbullet.py)
  * Stdout reporter with color on Windows: [colorama](https://github.com/tartley/colorama)
  * "browser" job kind: [requests-html](https://html.python-requests.org)
  * Unit testing: [pycodestyle](http://pycodestyle.pycqa.org/en/latest/)


QUICK START
-----------

 1. Start `urlwatch` to migrate your old data or start fresh
 2. Use `urlwatch --edit` to customize your job list (this will create/edit `urls.yaml`)
 3. Use `urlwatch --edit-config` if you want to set up e-mail sending
 4. Use `urlwatch --edit-hooks` if you want to write custom subclasses
 5. Add `urlwatch` to your crontab (`crontab -e`) to monitor webpages periodically

The checking interval is defined by how often you run `urlwatch`.
You can use e.g. [crontab.guru](https://crontab.guru) to figure out the
schedule expression for the checking interval, we recommend not more often
than 30 minutes (this would be `*/30 * * * *`). If you have never used
cron before, check out the
[crontab command help](https://www.computerhope.com/unix/ucrontab.htm).

On Windows, `cron` is not installed by default. Use the
[Windows Task Scheduler](https://en.wikipedia.org/wiki/Windows_Task_Scheduler)
instead, or see [this StackOverflow question](https://stackoverflow.com/q/132971/1047040)
for alternatives.


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

If you are using the `grep` filter, you can grep for a comma (`,`)
by using `\054` (`:` does not need to be escaped separately and
can be used as-is), for example to convert HTML to text, then grep
for `a,b:`, and then strip whitespace, use this:

```yaml
url: https://example.org/
filter: html2text,grep:a\054b:,strip
```

If you want to extract only the body tag you can use this filer:
```yaml
url: https://thp.io/2008/urlwatch/
filter: element-by-tag:body
```

You can also specify an external `diff`-style tool (a tool that takes
two filenames (old, new) as parameter and returns on its standard output
the difference of the files), for example to use GNU `wdiff` to get
word-based differences instead of line-based difference:

```yaml
url: https://example.com/
diff_tool: wdiff
```

Note that `diff_tool` specifies an external command-line tool, so that
tool must be installed separately (e.g. `apt install wdiff` on Debian or
`brew install wdiff` on macOS). Coloring is supported for `wdiff`-style
output, but potentially not for other diff tools.

To filter based on an [XPath](https://www.w3.org/TR/1999/REC-xpath-19991116/)
expression, you can use the `xpath` filter like so (see Microsoft's
[XPath Examples](https://msdn.microsoft.com/en-us/library/ms256086(v=vs.110).aspx)
page for some other examples):

```yaml
url: https://example.net/
filter: xpath:/body
```

This filters only the `<body>` element of the HTML document, stripping
out everything else.

To filter based on a [CSS selector](https://www.w3.org/TR/2011/REC-css3-selectors-20110929/),
you can use the `css` filter like so:

```yaml
url: https://example.net/
filter: css:body
```

Some limitations and extensions exist as explained in
[cssselect's documentation](https://cssselect.readthedocs.io/en/latest/#supported-selectors).

In some cases, it might be useful to ignore (temporary) network errors to
avoid notifications being sent. While there is a `display.error` config
option (defaulting to `True`) to control reporting of errors globally, to
ignore network errors for specific jobs only, you can use the
`ignore_connection_errors` key in the job list configuration file:

```yaml
url: https://example.com/
ignore_connection_errors: true
```

Similarly, you might want to ignore some (temporary) HTTP errors on the
server side:

```yaml
url: https://example.com/
ignore_http_error_codes: 408, 429, 500, 502, 503, 504
```

or ignore all HTTP errors if you like:

```yaml
url: https://example.com/
ignore_http_error_codes: 4xx, 5xx
```

For web pages with misconfigured HTTP headers or rare encodings, it may
be useful to explicitly specify an encoding from Python's
[Standard Encodings](https://docs.python.org/3/library/codecs.html#standard-encodings).

```yaml
url: https://example.com/
encoding: utf-8
```

By default, url jobs timeout after 60 seconds. If you want a different timeout
period, use the `timeout` key to specify it in number of seconds, or set it to 0
to never timeout.

```yaml
url: https://example.com/
timeout: 300
```

If you want to change some settings for all your jobs, edit the `job_defaults`
section in your config file:

```yaml
...
job_defaults:
  all:
    diff_tool: wdiff
  url:
    ignore_connection_errors: true
```
The above config file sets all jobs to use wdiff as diff tool, and all "url" jobs
to ignore connection errors.

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

To set up Telegram, from your Telegram app, chat up BotFather (New Message,
Search, "BotFather"), then say `/newbot` and follow the instructions.
Eventually it will tell you the bot token (in the form seen above,
`<number>:<random string>`) - add this to your config file.

You can then click on the link of your bot, which will send the message `/start`.
At this point, you can use the command `urlwatch --telegram-chats` to list the
private chats the bot is involved with. This is the chat ID that you need to put
into the config file as `chat_id`. You may add multiple chat IDs as a YAML list:
```yaml
telegram:
  bot_token: '999999999:3tOhy2CuZE0pTaCtszRfKpnagOG8IQbP5gf' # your bot api token
  chat_id:
    - '11111111'
    - '22222222'
  enabled: true
```

Don't forget to also enable the reporter.


SLACK
-----

Slack nofifications are configured using "Slack Incoming Webhooks". Here is a
sample configuration:

```yaml
slack:
  webhook_url: 'https://hooks.slack.com/services/T50TXXXXXU/BDVYYYYYYY/PWTqwyFM7CcCfGnNzdyDYZ'
  enabled: true
```

To set up Slack, from you Slack Team, create a new app and activate "Incoming Webhooks" on
a channel, you'll get a webhook URL, copy it into the configuration as seen above.

You can use the command `urlwatch --test-slack` to test if the Slack integration works.


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


E-MAIL VIA AMAZON SIMPLE EMAIL SERVICE (SES)
--------------------------------------------

Start the configuration editor: `urlwatch --edit-config`

These are the keys you need to configure:

- `report/email/enabled`: `true`
- `report/email/from`: `you@verified_domain.com` (edit accordingly)
- `report/email/method`: `smtp`
- `report/email/smtp/host`: `email-smtp.us-west-2.amazonaws.com` (edit accordingly)
- `report/email/smtp/user`: `ABCDEFGHIJ1234567890` (edit accordingly)
- `report/email/smtp/keyring`: `true`
- `report/email/smtp/port`: `587` (25 or 465 also work)
- `report/email/smtp/starttls`: `true`
- `report/email/to`: The e-mail address you want to send reports to

The password is not stored in the config file, but in your keychain. To store
the password, run: `urlwatch --smtp-login` and enter your password.


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


SENDING COOKIES
---------------

It is possible to add cookies to HTTP requests for pages that need it, the YAML
syntax for this is:

```yaml
url: http://example.com/
cookies:
    Key: ValueForKey
    OtherKey: OtherValue
```


WATCHING GITHUB RELEASES
------------------------

This is an example how to watch the GitHub "releases" page for a given
project for the latest release version, to be notified of new releases:

```yaml
url: "https://github.com/thp/urlwatch/releases/latest"
filter:
  - xpath: '(//div[contains(@class,"release-timeline-tags")]//h4)[1]/a'
  - html2text: re
```


USING XPATH AND CSS FILTERS WITH XML
--------------------------------

By default, XPath and CSS filters are set up for HTML documents. However,
it is possible to use them for XML documents as well (these examples parse
an RSS feed and filter only the titles and publication dates):

```yaml
url: 'https://heronebag.com/blog/index.xml'
filter:
  - xpath:
      path: '//item/title/text()|//item/pubDate/text()'
      method: xml
```
```yaml
url: 'https://heronebag.com/blog/index.xml'
filter:
  - css:
      selector: 'item > title, item > pubDate'
      method: xml
  - html2text: re
```


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


CONTACT
-------

Website: https://thp.io/2008/urlwatch/

E-Mail: m@thp.io
