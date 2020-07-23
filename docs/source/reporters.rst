.. _reporters:

Reporters
=========

By default `urlwatch` prints out information about changes to standard
output, which is your terminal if you run it interactively. If running
via `cron` or another scheduler service, it depends on how the scheduler
is configured.

You can enable one or more additional reporters that are used to send
change notifications. Please note that most reporters need additional
dependencies installed.

Built-in reporters
------------------

The list of built-in reporters can be retrieved using::

    urlwatch --features

At the moment, the following reporters are built-in:

- **stdout**: Print summary on stdout (the console)
- **email**: Send summary via e-mail / SMTP
- **mailgun**: Custom email reporter that uses Mailgun
- **matrix**: Custom Matrix reporter
- **pushbullet**: Send summary via pushbullet.com
- **pushover**: Send summary via pushover.net
- **slack**: Custom Slack reporter
- **telegram**: Custom Telegram reporter
- **ifttt**: Send summary via IFTTT

.. To convert the "urlwatch --features" output, use:
   sed -e 's/^  \* \(.*\) - \(.*\)$/- **\1**: \2/'


Pushover
--------

You can configure urlwatch to send real time notifications about changes
via Pushover(https://pushover.net/). To enable this, ensure you have the
chump python package installed (see DEPENDENCIES). Then edit your config
(``urlwatch --edit-config``) and enable pushover. You will also need to
add to the config your Pushover user key and a unique app key (generated
by registering urlwatch as an application on your Pushover
account(https://pushover.net/apps/build).

You can send to a specific device by using the device name, as indicated
when you add or view your list of devices in the Pushover console. For
example ``device:  'MyPhone'``, or ``device: 'MyLaptop'``. To send to
*all* of your devices, set ``device: null`` in your config
(``urlwatch --edit-config``) or leave out the device configuration
completely.

Pushbullet
----------

Pushbullet notifications are configured similarly to Pushover (see
above). You’ll need to add to the config your Pushbullet Access Token,
which you can generate at https://www.pushbullet.com/#settings

Telegram
--------

Telegram notifications are configured using the Telegram Bot API. For
this, you’ll need a Bot API token and a chat id (see
https://core.telegram.org/bots). Sample configuration:

.. code:: yaml

   telegram:
     bot_token: '999999999:3tOhy2CuZE0pTaCtszRfKpnagOG8IQbP5gf' # your bot api token
     chat_id: '88888888' # the chat id where the messages should be sent
     enabled: true

To set up Telegram, from your Telegram app, chat up BotFather (New
Message, Search, “BotFather”), then say ``/newbot`` and follow the
instructions. Eventually it will tell you the bot token (in the form
seen above, ``<number>:<random string>``) - add this to your config
file.

You can then click on the link of your bot, which will send the message
``/start``. At this point, you can use the command
``urlwatch --telegram-chats`` to list the private chats the bot is
involved with. This is the chat ID that you need to put into the config
file as ``chat_id``. You may add multiple chat IDs as a YAML list:

.. code:: yaml

   telegram:
     bot_token: '999999999:3tOhy2CuZE0pTaCtszRfKpnagOG8IQbP5gf' # your bot api token
     chat_id:
       - '11111111'
       - '22222222'
     enabled: true

Don’t forget to also enable the reporter.

Slack
-----

Slack notifications are configured using “Slack Incoming Webhooks”. Here
is a sample configuration:

.. code:: yaml

   slack:
     webhook_url: 'https://hooks.slack.com/services/T50TXXXXXU/BDVYYYYYYY/PWTqwyFM7CcCfGnNzdyDYZ'
     enabled: true

To set up Slack, from you Slack Team, create a new app and activate
“Incoming Webhooks” on a channel, you’ll get a webhook URL, copy it into
the configuration as seen above.

You can use the command ``urlwatch --test-slack`` to test if the Slack
integration works.

IFTTT
----------

IFTTT notifications are configured similarly to Slack (see
above). You’ll need to retrieve your webhook url from your IFTTT account.

Visit https://ifttt.com/maker_webhooks/settings to retrieve your key.

`webhook_url` is of form https://maker.ifttt.com/trigger/{event_name_you_want}/with/key/{your_key}

Matrix
------

You can have notifications sent to you through the Matrix protocol.

To achieve this, you first need to register a Matrix account for the bot
on any homeserver.

You then need to acquire an access token and room ID, using the
following instructions adapted from `this
guide <https://t2bot.io/docs/access_tokens/>`__:

1. Open `Riot.im <https://riot.im/app/>`__ in a private browsing window
2. Register/Log in as your bot, using its user ID and password.
3. Set the display name and avatar, if desired.
4. In the settings page, scroll down to the bottom and click Access
   Token: <click to reveal>.
5. Copy the highlighted text to your configuration.
6. Join the room that you wish to send notifications to.
7. Go to the Room Settings (gear icon) and copy the *Internal Room ID*
   from the bottom.
8. Close the private browsing window **but do not log out, as this
   invalidates the Access Token**.

Here is a sample configuration:

.. code:: yaml

   matrix:
     homeserver: https://matrix.org
     access_token: "YOUR_TOKEN_HERE"
     room_id: "!roomroomroom:matrix.org"
     enabled: true

You will probably want to use the following configuration for the
``markdown`` reporter, if you intend to post change notifications to a
public Matrix room, as the messages quickly become noisy:

.. code:: yaml

   markdown:
     details: false
     footer: false
     minimal: true
     enabled: true

E-Mail via GMail SMTP
---------------------

You need to configure your GMail account to allow for “less secure”
(password-based) apps to login:

1. Go to https://myaccount.google.com/
2. Click on “Sign-in & security”
3. Scroll all the way down to “Allow less secure apps” and enable it

Now, start the configuration editor: ``urlwatch --edit-config``

These are the keys you need to configure (see #158):

-  ``report/email/enabled``: ``true``
-  ``report/email/from``: ``your.username@gmail.com`` (edit accordingly)
-  ``report/email/method``: ``smtp``
-  ``report/email/smtp/host``: ``smtp.gmail.com``
-  ``report/email/smtp/auth``: ``true``
-  ``report/email/smtp/port``: ``587``
-  ``report/email/smtp/starttls``: ``true``
-  ``report/email/to``: The e-mail address you want to send reports to

Now, for setting the password, it’s not stored in the config file, but
in your keychain. To store the password, run: ``urlwatch --smtp-login``
and enter your password.

E-Mail via Amazon Simple E-Mail Service (SES)
---------------------------------------------

Start the configuration editor: ``urlwatch --edit-config``

These are the keys you need to configure:

-  ``report/email/enabled``: ``true``
-  ``report/email/from``: ``you@verified_domain.com`` (edit accordingly)
-  ``report/email/method``: ``smtp``
-  ``report/email/smtp/host``: ``email-smtp.us-west-2.amazonaws.com``
   (edit accordingly)
-  ``report/email/smtp/user``: ``ABCDEFGHIJ1234567890`` (edit
   accordingly)
-  ``report/email/smtp/auth``: ``true``
-  ``report/email/smtp/port``: ``587`` (25 or 465 also work)
-  ``report/email/smtp/starttls``: ``true``
-  ``report/email/to``: The e-mail address you want to send reports to

The password is not stored in the config file, but in your keychain. To
store the password, run: ``urlwatch --smtp-login`` and enter your
password.


SMTP login without keyring
--------------------------

If for whatever reason you cannot use a keyring to store your password
(for example, when using it from a ``cron`` job) you can also set the
``insecure_password`` option in the SMTP config:

-  ``report/email/smtp/auth``: ``true``
-  ``report/email/smtp/insecure_password``: ``secret123``

The ``insecure_password`` key will be preferred over the data stored in
the keyring. Please note that as the name says, storing the password as
plaintext in the configuration is insecure and bad practice, but for an
e-mail account that’s only dedicated for sending mails this might be a
way. **Never ever use this with your your primary e-mail account!**
Seriously! Create a throw-away GMail (or other) account just for sending
out those e-mails or use local ``sendmail`` with a mail server
configured instead of relying on SMTP and password auth.

Note that this makes it really easy for your password to be picked up by
software running on your machine, by other users logged into the system
and/or for the password to appear in log files accidentally.


