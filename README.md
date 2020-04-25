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

  * Python 3.5 or newer
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
  * Matrix reporter: [matrix_client](https://github.com/matrix-org/matrix-python-sdk), [markdown2](https://github.com/trentm/python-markdown2)
  * Stdout reporter with color on Windows: [colorama](https://github.com/tartley/colorama)
  * "browser" job kind: [requests-html](https://html.python-requests.org)
  * Unit testing: [pycodestyle](http://pycodestyle.pycqa.org/en/latest/)
  * Beautify filter : [beautifulsoup4](https://pypi.org/project/beautifulsoup4/) [jsbeautifier](https://pypi.org/project/jsbeautifier/) [cssbeautifier](https://pypi.org/project/cssbeautifier/)


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

If you want to extract only the body tag you can use this filter:
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

Sometimes a web page can have the same data between comparisons but it appears in random order.
If that happens, you can choose to sort before the comparison.
```yaml
url: https://example.net/
filter: sort
```

You can choose to reverse the items before the comparison transactions.
```yaml
url: https://example.net/
filter:
- reverse:
- html2text: re
```

PUSHOVER
--------

You can configure urlwatch to send real time notifications about changes
via Pushover(https://pushover.net/). To enable this, ensure you have the
chump python package installed (see DEPENDENCIES). Then edit your config
(`urlwatch --edit-config`) and enable pushover. You will also need to add
to the config your Pushover user key and a unique app key (generated by
registering urlwatch as an application on your Pushover account(https://pushover.net/apps/build).

You can send to a specific device by using the device name, as indicated when
you add or view your list of devices in the Pushover console.  For example
`device:  'MyPhone'`, or `device: 'MyLaptop'`. To send to *all* of your
devices, set `device: null` in your config (`urlwatch --edit-config`) or leave
out the device configuration completely.


PUSHBULLET
--------

Pushbullet notifications are configured similarly to Pushover (see above).
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

Slack notifications are configured using "Slack Incoming Webhooks". Here is a
sample configuration:

```yaml
slack:
  webhook_url: 'https://hooks.slack.com/services/T50TXXXXXU/BDVYYYYYYY/PWTqwyFM7CcCfGnNzdyDYZ'
  enabled: true
```

To set up Slack, from you Slack Team, create a new app and activate "Incoming Webhooks" on
a channel, you'll get a webhook URL, copy it into the configuration as seen above.

You can use the command `urlwatch --test-slack` to test if the Slack integration works.


MATRIX
------

You can have notifications sent to you through the Matrix protocol.

To achieve this, you first need to register a Matrix account for the bot on any homeserver.

You then need to acquire an access token and room ID, using the following instructions adapted from [this guide](https://t2bot.io/docs/access_tokens/):

1. Open [Riot.im](https://riot.im/app/) in a private browsing window
2. Register/Log in as your bot, using its user ID and password.
3. Set the display name and avatar, if desired.
4. In the settings page, scroll down to the bottom and click Access Token: \<click to reveal\>.
5. Copy the highlighted text to your configuration.
6. Join the room that you wish to send notifications to.
7. Go to the Room Settings (gear icon) and copy the *Internal Room ID* from the bottom.
8. Close the private browsing window **but do not log out, as this invalidates the Access Token**.

Here is a sample configuration:

```yaml
matrix:
  homeserver: https://matrix.org
  access_token: "YOUR_TOKEN_HERE"
  room_id: "!roomroomroom:matrix.org"
  enabled: true
```

You will probably want to use the following configuration for the `markdown` reporter, if you intend to post change
notifications to a public Matrix room, as the messages quickly become noisy:

```yaml
markdown:
  details: false
  footer: false
  minimal: true
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
- `report/email/smtp/auth`: `true`
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
- `report/email/smtp/auth`: `true`
- `report/email/smtp/port`: `587` (25 or 465 also work)
- `report/email/smtp/starttls`: `true`
- `report/email/to`: The e-mail address you want to send reports to

The password is not stored in the config file, but in your keychain. To store
the password, run: `urlwatch --smtp-login` and enter your password.


SMTP LOGIN WITHOUT KEYRING
--------------------------

If for whatever reason you cannot use a keyring to store your password
(for example, when using it from a `cron` job)
you can also set the `insecure_password` option in the SMTP config:

- `report/email/smtp/auth`: `true`
- `report/email/smtp/insecure_password`: `secret123`

The `insecure_password` key will be preferred over the data stored in
the keyring. Please note that as the name says, storing the password
as plaintext in the configuration is insecure and bad practice, but
for an e-mail account that's only dedicated for sending mails this
might be a way. **Never ever use this with your your primary
e-mail account!** Seriously! Create a throw-away GMail (or other)
account just for sending out those e-mails or use local `sendmail` with
a mail server configured instead of relying on SMTP and password auth.

Note that this makes it really easy for your password to be picked up
by software running on your machine, by other users logged into the system
and/or for the password to appear in log files accidentally.


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


USING XPATH AND CSS FILTERS WITH XML AND EXCLUSIONS
---------------------------------------------------

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

To match an element in an [XML namespace](https://www.w3.org/TR/xml-names/),
use a namespace prefix before the tag name. Use a `:` to seperate the namespace
prefix and the tag name in an XPath expression, and use a `|` in a CSS selector.
```yaml
url: 'https://www.wired.com/feed/rss'
filter:
  - xpath:
      path: '//item/media:keywords'
      method: xml
      namespaces:
        media: http://search.yahoo.com/mrss/
```
```yaml
url: 'https://www.wired.com/feed/rss'
filter:
  - css:
      selector: 'item > media|keywords'
      method: xml
      namespaces:
        media: http://search.yahoo.com/mrss/
```
Alternatively, use the XPath expression `//*[name()='<tag_name>']` to bypass
the namespace entirely.

Another useful option with XPath and CSS filters is `exclude`. Elements selected
by this `exclude` expression are removed from the final result. For example, the
following job will not have any `<a>` tag in its results:

```yaml
url: https://example.org/
filter:
  - css:
      selector: 'body'
      exclude: 'a'
```


COMPARE WITH SEVERAL LATEST SNAPSHOTS
-------------------------------------
If a webpage frequently changes between several known stable states, it may be
desirable to have changes reported only if the webpage changes into a new
unknown state. You can use `compared_versions` to do this.

```yaml
url: https://example.com/
compared_versions: 3
```

In this example, changes are only reported if the webpage becomes different from
the latest three distinct states. The differences are shown relative to the
closest match.


REMOVE OR REPLACE TEXT USING REGULAR EXPRESSIONS
------------------------------------------------

Just like Python's `re.sub` function, there's the possibility to apply a regular
expression and either remove of replace the matched text. The following example
applies the filter 3 times:

 1. Just specifying a string as the value will replace the matches with the empty string.
 2. Simple patterns can be replaced with another string using "pattern" as the expression and "repl" as the replacement.
 3. You can use groups (`()`) and back-reference them with `\1` (etc..) to put groups into the replacement string.

All features are described in Python's [re.sub](https://docs.python.org/3/library/re.html#re.sub)
documentation (the `pattern` and `repl` values are passed to this function as-is, with the value
of `repl` defaulting to the empty string).


```yaml
kind: url
url: https://example.com/
filter:
    - re.sub: '\s*href="[^"]*"'
    - re.sub:
        pattern: '<h1>'
        repl: 'HEADING 1: '
    - re.sub:
        pattern: '</([^>]*)>'
        repl: '<END OF TAG \1>'
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
