.. _introduction:

Introduction
============


Quick Start
-----------

First, install urlwatch by following :doc:`installation`. Once installed:

1. Run ``urlwatch`` once to migrate your old data or start fresh
2. Use ``urlwatch --edit`` to customize jobs and filters (``urls.yaml``)
3. Use ``urlwatch --edit-config`` to customize settings and reporters (``urlwatch.yaml``)
4. Add ``urlwatch`` to your crontab (``crontab -e``) to monitor webpages periodically

The checking interval is defined by how often you run ``urlwatch``. You
can use e.g. `crontab.guru <https://crontab.guru>`__ to figure out the
schedule expression for the checking interval, we recommend not more
often than 30 minutes (this would be ``*/30 * * * *``). If you have
never used cron before, check out the `crontab command
help <https://www.computerhope.com/unix/ucrontab.htm>`__.

On Windows, ``cron`` is not installed by default. Use the `Windows Task
Scheduler <https://en.wikipedia.org/wiki/Windows_Task_Scheduler>`__
instead, or see `this StackOverflow
question <https://stackoverflow.com/q/132971/1047040>`__ for
alternatives.


How it works
------------

Every time you run :manpage:`urlwatch(1)`, it:

- retrieves the output of each job and filters it
- compares it with the version retrieved the previous time ("diffing")
- if it finds any differences, it invokes enabled reporters (e.g.
  text reporter, e-mail reporter, ...) to notify you of the changes

Jobs and Filters
----------------

Each website or shell command to be monitored constitutes a "job".

The instructions for each such job are contained in a config file in the `YAML
format`_. If you have more than one job, you separate them with a line
containing only ``---``.

You can edit the job and filter configuration file using:

.. code::

    urlwatch --edit

If you get an error, set your ``$EDITOR`` (or ``$VISUAL``) environment
variable in your shell, for example:

.. code::

    export EDITOR=/bin/nano

While you can edit the YAML file manually, using ``--edit`` will
do sanity checks before activating the new configuration file.

.. _YAML format: https://yaml.org/spec/

Kinds of Jobs
~~~~~~~~~~~~~

Each job must have exactly one of the following keys, which also
defines the kind of job:

- ``url`` retrieves what is served by the web server (HTTP GET by default),
- ``navigate`` uses a headless browser to load web pages requiring JavaScript, and
- ``command`` runs a shell command.

Each job can have an optional ``name`` key to define a user-visible name for the job.

You can then use optional keys to finely control various job's parameters.

.. only:: man

    See :manpage:`urlwatch-jobs(5)` for detailed information on job configuration.

Filters
~~~~~~~

You may use the ``filter`` key to select one or more :doc:`filters` to apply to
the data after it is retrieved, for example to:

- select HTML: ``css``, ``xpath``, ``element-by-class``, ``element-by-id``, ``element-by-style``, ``element-by-tag``
- make HTML more readable: ``html2text``, ``beautify``
- make PDFs readable: ``pdf2text``
- make JSON more readable: ``format-json``
- make iCal more readable: ``ical2text``
- make binary readable: ``hexdump``
- just detect changes: ``sha1sum``
- edit text: ``grep``, ``grepi``, ``strip``, ``sort``, ``striplines``

These filters can be chained. As an example, after retrieving an HTML
document by using the ``url`` key, you can extract a selection with the
``xpath`` filter, convert this to text with ``html2text``, use ``grep`` to
extract only lines matching a specific regular expression, and then ``sort``
them:

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

.. only:: man

    See :manpage:`urlwatch-filters(5)` for detailed information on filter configuration.

Reporters
---------

`urlwatch` can be configured to do something with its report besides
(or in addition to) the default of displaying it on the console.

:doc:`reporters` are configured in the global configuration file:

.. code::

    urlwatch --edit-config

Examples of reporters:

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
- ``shell``

.. only:: man

    See :manpage:`urlwatch-reporters(5)` for reporter configuration options.

.. only:: man

    See Also
    --------

    :manpage:`urlwatch(1)`,
    :manpage:`urlwatch-jobs(5)`,
    :manpage:`urlwatch-filters(5)`,
    :manpage:`urlwatch-config(5)`,
    :manpage:`urlwatch-reporters(5)`,
    :manpage:`cron(8)`
