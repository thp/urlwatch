.. _reporters:

Reporters
=========

.. only:: man

   Synopsis
   --------

   urlwatch --edit-config

   Description
   -----------


By default :manpage:`urlwatch(1)` prints out information about changes to standard
output, which is your terminal if you run it interactively. If running
via :manpage:`cron(8)` or another scheduler service, it depends on how the scheduler
is configured.

You can enable one or more additional reporters that are used to send
change notifications. Please note that most reporters need additional
dependencies installed.

.. only:: html or pdf

    See :ref:`configuration` on how to edit the configuration.

.. only:: man

    See :manpage:`urlwatch-config(5)` for generic config settings.

To send a test notification, use the ``--test-reporter`` command-line option
with the name of the reporter::

    urlwatch --test-reporter stdout

This will create a test report with ``new``, ``changed``, ``unchanged`` and
``error`` notifications (only the ones configured in ``display`` in the
:ref:`configuration` will be shown in the report) and send it via the
``stdout`` reporter (if it is enabled).

To test if your e-mail reporter is configured correctly, you can use::

   urlwatch --test-reporter email

Any reporter that is configured and enabled can be tested.

If the notification does not work, check your configuration and/or add
the ``--verbose`` command-line option to show detailed debug logs.


Built-in reporters
------------------

The list of built-in reporters can be retrieved using::

    urlwatch --features

At the moment, the following reporters are built-in:

- **discord**: Send a message to a Discord channel
- **email**: Send summary via e-mail / SMTP / sendmail
- **gotify**: Send a message to a gotify server
- **ifttt**: Send summary via IFTTT
- **mailgun**: Send e-mail via the Mailgun service
- **matrix**: Send a message to a room using the Matrix protocol
- **mattermost**: Send a message to a Mattermost channel
- **prowl**: Send a detailed notification via prowlapp.com
- **pushbullet**: Send summary via pushbullet.com
- **pushover**: Send summary via pushover.net
- **shell**: Pipe a message to a shell command
- **slack**: Send a message to a Slack channel
- **stdout**: Print summary on stdout (the console)
- **telegram**: Send a message using Telegram
- **xmpp**: Send a message using the XMPP Protocol

.. To convert the "urlwatch --features" output, use:
   sed -e 's/^  \* \(.*\) - \(.*\)$/- **\1**: \2/'


Pushover
--------

You can configure urlwatch to send real time notifications about changes
via `Pushover`_. To enable this, ensure you have the
``chump`` python package installed (see :doc:`dependencies`). Then edit your config
(``urlwatch --edit-config``) and enable pushover. You will also need to
add to the config your Pushover user key and a unique app key (generated
by registering urlwatch as an application on your `Pushover account`_.

.. _Pushover: https://pushover.net/
.. _Pushover account: https://pushover.net/apps/build

You can send to a specific device by using the device name, as indicated
when you add or view your list of devices in the Pushover console. For
example ``device:  'MyPhone'``, or ``device: 'MyLaptop'``. To send to
*all* of your devices, set ``device: null`` in your config
(``urlwatch --edit-config``) or leave out the device configuration
completely.

Setting the priority is possible via the ``priority`` config option, which
can be ``lowest``, ``low``, ``normal``, ``high`` or ``emergency``. Any
other setting (including leaving the option unset) maps to ``normal``.

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

Messages can be sent silently (``silent``) if you prefer notifications
with no sounds, and monospace formatted (``monospace``).
By default notifications are not silent and no formatting is done.

.. code:: yaml

   telegram:
     # ...
     silent: true # message is sent silently
     monospace: true # display message as pre-formatted code block

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

Mattermost
----------

Mattermost notifications are set up the same way as Slack notifications,
the webhook URL is different:

.. code:: yaml

   mattermost:
     webhook_url: 'http://{your-mattermost-site}/hooks/XXXXXXXXXXXXXXXXXXXXXX'
     enabled: true

See `Incoming Webooks <https://developers.mattermost.com/integrate/incoming-webhooks/>`__
in the Mattermost documentation for details.

Discord
-------

Discord notifications are configured using “Discord Incoming Webhooks”. Here
is a sample configuration:

.. code:: yaml

   discord:
      webhook_url: 'https://discordapp.com/api/webhooks/11111XXXXXXXXXXX/BBBBYYYYYYYYYYYYYYYYYYYYYYYyyyYYYYYYYYYYYYYY'
      enabled: true
      embed: true
      colored: true
      subject: '{count} changes: {jobs}'

To set up Discord, from your Discord Server settings, select Integration and then create a "New Webhook", give the webhook a name to post under, select a channel, push "Copy Webhook URL" and paste it into the configuration as seen above.

Embedded content might be easier to read and identify individual reports. Subject precedes the embedded report and is only used when `embed` is true.

When `colored` is true reports will be embedded in code section (with diff syntax) to enable colors.

Gotify
------

[Gotify](https://gotify.net/) is a server for sending and receiving messages in real-time through WebSockets.

To push notifications to a gotify server you need an application token.

You can create one for urlwatch like so:

1. Log into your gotify server's Web-UI.
2. Navigate to the “APPS” tab.
3. Click on the “CREATE APPLICATION” button.
4. Fill out the fields and press “CREATE”.
6. Click on the eye icon of the newly created entry and copy the token.

Here is a sample configuration:

.. code:: yaml

   gotify:
     enabled: true
     priority: 4
     server_url: "http://127.0.0.1:8090"
     title: null
     token: "Aa1yyikLFjEm35A"

IFTTT
-----

To configure IFTTT events, you need to retrieve your key from here:

https://ifttt.com/maker_webhooks/settings

The URL shown in "Account Info" has the following format:

.. code::

   https://maker.ifttt.com/use/{key}

In this URL, ``{key}`` is your API key. The configuration should look like
this (you can pick any event name you want):

.. code:: yaml

   ifttt:
     enabled: true
     key: aA12abC3D456efgHIjkl7m
     event: event_name_you_want

The event will contain three values in the posted JSON:

* ``value1``: The type of change (``new``, ``changed``, ``unchanged`` or ``error``)
* ``value2``: The name of the job (``name`` key in ``jobs.yaml``)
* ``value3``: The location of the job (``url``, ``command`` or ``navigate`` key in ``jobs.yaml``)

These values will be passed on to the Action in your Recipe.


Matrix
------

You can have notifications sent to you through the `Matrix protocol`_.

.. _Matrix protocol: https://matrix.org

To achieve this, you first need to register a Matrix account for the bot
on any homeserver.

You then need to acquire an access token and room ID, using the
following instructions adapted from `this
guide <https://t2bot.io/docs/access_tokens/>`__:

1. Open `Riot.im <https://riot.im/app/>`__ in a private browsing window
2. Register/Log in as your bot, using its user ID and password.
3. Set the display name and avatar, if desired.
4. In the settings page, select the "Help & About" tab, scroll down to the bottom and click Access
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

E-Mail via sendmail
---------------------

You can send email via the system's ``sendmail`` command provided by the MTA. You need to set ``method: sendmail`` in the config file:

.. code:: yaml

    report:
      email:
        enabled: true
        from: 'postmaster@example.com'
        to: 'recipient@bar.com'
        method: sendmail


E-Mail via GMail SMTP
---------------------

You need to configure your GMail account to allow for “less secure”
(password-based) apps to login:

1. Go to https://myaccount.google.com/
2. Click on “Sign-in & security”
3. Scroll all the way down to “Allow less secure apps” and enable it

You do not want to do this with your primary GMail account, but
rather on a separate account that you create just for sending mails
via urlwatch. Allowing less secure apps and storing the password
(even if it's in the keychain) is not good security practice for your
primary account.

Now, start the configuration editor::

    urlwatch --edit-config

These are the keys you need to configure:

.. code:: yaml

    report:
      email:
        enabled: true
        from: your.username@gmail.com
        to: your.destination.email@example.com
        method: smtp
        smtp:
          host: smtp.gmail.com
          auth: true
          port: 587
          starttls: true

The password is best stored in your keychain, and not in the config
file. To store the password, run::

    urlwatch --smtp-login

This will query your password, check the login, and store it in your
keychain. Subsequent runs will use this password for logging in.


E-Mail via Amazon Simple E-Mail Service (SES)
---------------------------------------------

Same as the GMail configuration above, but use e.g.
``email-smtp.us-west-2.amazonaws.com`` as the SMTP host, and
username and port settings according to SES's login page.


.. _smtp-login-without-keyring:

SMTP login without keyring
--------------------------

If for whatever reason you cannot use a keyring to store your password
(for example, when using it from a ``cron`` job) you can also set the
``insecure_password`` option in the SMTP config:

.. code:: yaml

    report:
      email:
        smtp:
          auth: true
          insecure_password: secret123

The ``insecure_password`` key will be preferred over the data stored in
the keyring. Please note that as the name says, storing the password as
plaintext in the configuration is insecure and bad practice, but for an
e-mail account that’s only dedicated for sending mails this might be a
way. **Never ever use this with your primary e-mail account!**
Seriously! Create a throw-away GMail (or other) account just for sending
out those e-mails or use local ``sendmail`` with a mail server
configured instead of relying on SMTP and password auth.

Note that this makes it really easy for your password to be picked up by
software running on your machine, by other users logged into the system
and/or for the password to appear in log files accidentally.

XMPP
----

You can have notifications sent to you through the `XMPP protocol`.

To achieve this, you should register a new XMPP account that is just
used for urlwatch.

Here is a sample configuration:

.. code:: yaml

   xmpp:
     enabled: true
     sender: "BOT_ACCOUNT_NAME"
     recipient: "YOUR_ACCOUNT_NAME"

The password is not stored in the config file, but in your keychain. To
store the password, run: ``urlwatch --xmpp-login`` and enter your
password.

If for whatever reason you cannot use a keyring to store your password
you can also set the ``insecure_password`` option in the XMPP config.
For more information about the security implications, see
:ref:`smtp-login-without-keyring`.

Prowl
-----

You can have notifications sent to you through the `Prowl` push
notification service, to receive the notification on iOS.

To achieve this, you should register a new Prowl account, and have
the Prowl application installed on your iOS device.

To create an API key for urlwatch:

1. Log into the Prowl website at https://prowlapp.com/
2. Navigate to the “API Keys” tab.
3. Scroll to the “Generate a new API key” section.
4. Give the key a note that will remind you you've used it for urlwatch.
5. Press “Generate Key”
6. Copy the resulting key.

Here is a sample configuration:

.. code:: yaml

   prowl:
     enabled: true
     api_key: '<your api key here>'
     priority: 2
     application: 'urlwatch example'
     subject: '{count} changes: {jobs}'

The “subject" field is similar to the subject field in the email, and
will be used as the name of the Prowl event. The application is prepended
to the event and shown as the source of the event in the Prowl App.


Shell
-----

This is a simple reporter that pipes the text report notification to a
command of your choice. The command is run using Python's
`subprocess.Popen()`_ with ``shell=False`` (to avoid possibly-unwanted
shell expansion). Of course, you can create your own shell script that
does shell expansion and other things, and call that from the ``command``.

The key ``ignore_stdout`` (defaults to ``true``) can be used to ignore
any output the program writes on stdout. The key ``ignore_stderr`` (defaults
to ``false``) can be used to ignore any output the program writes on stderr.

If stdout/stderr are not ignored, urlwatch will log any possible output
in its ``--verbose`` log.

The report written to ``stdin`` of the process is based on the output of
the ``text`` reporter, configuring the text reporter will adjust the data
sent to the ``shell`` reporter.

For example, to simply append reports to a file, configure it like this:

.. code:: yaml

    shell:
      enabled: true
      command: ['tee', '-a', '/path/to/log.txt']
      ignore_stdout: true

.. _subprocess.Popen(): https://docs.python.org/3/library/subprocess.html#popen-constructor


.. only:: man

    Files
    -----

    ``$XDG_CONFIG_HOME/urlwatch/urlwatch.yaml``

    See also
    --------

    :manpage:`urlwatch(1)`,
    :manpage:`urlwatch-config(5)`,
    :manpage:`urlwatch-intro(7)`,
    :manpage:`urlwatch-cookbook(7)`
