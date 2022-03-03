.. _introduction:

Introduction
============

`urlwatch` monitors the output of webpages or arbitrary shell commands.

Every time you run `urlwatch`, it:

- retrieves the output and processes it
- compares it with the version retrieved the previous time ("diffing")
- if it finds any differences, generates a summary "report" that can be displayed or sent via one or more methods, such as email

:ref:`Jobs`
-----------
Each website or shell command to be monitored constitutes a "job".

The instructions for each such job are contained in a config file in the `YAML format`_, accessible with the ``urlwatch --edit`` command.
If you get an error, set your ``$EDITOR`` (or ``$VISUAL``) environment
variable in your shell with a command such as ``export EDITOR=/bin/nano``.

.. _YAML format: https://yaml.org/spec/

Typically, the first entry ("key") in a job is a ``name``, which can be anything you want and helps you identify what you're monitoring.

The second key is one of either ``url``, ``navigate`` or ``command``:

- ``url`` retrieves what is served by the web server,
- ``navigate`` handles more web pages requiring JavaScript to display the content to be monitored, and
- ``command`` runs a shell command.

You can then use optional keys to finely control various job's parameters.

Finally, you often use the ``filter`` key to select one or more :ref:`filters` to apply to the data after it is retrieved, to:

- select HTML: ``css``, ``xpath``, ``element-by-class``, ``element-by-id``, ``element-by-style``, ``element-by-tag``
- make HTML more readable: ``html2text``, ``beautify``
- make PDFs readable: ``pdf2text``
- make JSON more readable: ``format-json``
- make iCal more readable: ``ical2text``
- make binary readable: ``hexdump``
- just detect changes: ``sha1sum``
- edit text: ``grep``, ``grepi``, ``strip``, ``sort``, ``striplines``

These :ref:`filters` can be chained. As an example, after retrieving an HTML document by using the ``url`` key, you can extract a selection with the ``xpath`` filter, convert this to text with ``html2text``, use ``grep`` to extract only lines matching a specific regular expression, and then ``sort`` them:

.. code-block:: yaml

    name: "Sample urlwatch job definition"
    url: "https://example.dummy/"
    https_proxy: "http://dummy.proxy/"
    max_tries: 2
    filter:
      - xpath: '//section[@role="main"]'
      - html2text:
          method: pyhtml2text
          unicode_snob: true
          body_width: 0
          inline_links: false
          ignore_links: true
          ignore_images: true
          pad_tables: false
          single_line_break: true
      - grep: "lines I care about"
      - sort:
    ---

If you have more than one job, per `YAML specifications <https://yaml.org/spec/>`__, you separate them with a line containing only ``---``.

:ref:`Reporters`
----------------
`urlwatch` can be configured to do something with its report besides (or in addition to) the default of displaying it on the console, such as one or more of:

- ``email`` (using SMTP)
- email using ``mailgun``
- ``slack``
- ``discord``
- ``pushbullet``
- ``telegram``
- ``matrix``
- ``pushover``
- ``stdout``
- ``xmpp``

Reporters are configured in a separate file, see :ref:`configuration`.
