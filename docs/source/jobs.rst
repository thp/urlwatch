.. _jobs:

Jobs
====

.. only:: man

   Synopsis
   --------

   urlwatch --edit

   Description
   -----------

Jobs are the kind of things that :manpage:`urlwatch(1)` can monitor.

The list of jobs to run are contained in the configuration file ``urls.yaml``,
accessed with the command ``urlwatch --edit``, each separated by a line
containing only ``---``. The command ``urlwatch --list`` prints the name
of each job, along with its index number (1, 2, 3, ...) which gets assigned
automatically according to its position in the configuration file.

While optional, it is recommended that each job starts with a ``name`` entry:

.. code-block:: yaml

    name: "This is a human-readable name/label of the job"

The following job types are available:


URL
---

This is the main job type -- it retrieves a document from a web server:

.. code-block:: yaml

    name: "urlwatch homepage"
    url: "https://thp.io/2008/urlwatch/"

Required keys:

- ``url``: The URL to the document to watch for changes

Job-specific optional keys:

- ``cookies``: Cookies to send with the request (see :ref:`advanced_topics`)
- ``method``: HTTP method to use (default: ``GET``)
- ``data``: HTTP POST/PUT data
- ``ssl_no_verify``: Do not verify SSL certificates (true/false)
- ``ignore_cached``: Do not use cache control (ETag/Last-Modified) values (true/false)
- ``http_proxy``: Proxy server to use for HTTP requests (might be http:// or socks5://)
- ``https_proxy``: Proxy server to use for HTTPS requests (might be http:// or socks5://)
- ``headers``: HTTP header to send along with the request
- ``encoding``: Override the character encoding from the server (see :ref:`advanced_topics`)
- ``timeout``: Override the default socket timeout (see :ref:`advanced_topics`)
- ``ignore_connection_errors``: Ignore (temporary) connection errors (see :ref:`advanced_topics`)
- ``ignore_http_error_codes``: List of HTTP errors to ignore (see :ref:`advanced_topics`)
- ``ignore_timeout_errors``: Do not report errors when the timeout is hit
- ``ignore_too_many_redirects``: Ignore redirect loops (see :ref:`advanced_topics`)

(Note: ``url`` implies ``kind: url``)


Browser
-------

This job type is a resource-intensive variant of "URL" to handle web pages that
require JavaScript to render the content being monitored.

The optional `playwright` package must be installed in order to run Browser jobs
(see :ref:`dependencies`). You will also need to install the browsers using
``playwright install`` (see `Playwright Installation`_ for details).

.. _`Playwright Installation`: https://playwright.dev/python/docs/intro

.. code-block:: yaml

   name: "A page with JavaScript"
   navigate: "https://example.org/"

Required keys:

- ``navigate``: URL to navigate to with the browser

Job-specific optional keys:

- ``wait_until``: Either ``load``, ``domcontentloaded``, ``networkidle``, or
  ``commit`` (see :ref:`advanced_topics`)
- ``useragent``: ``User-Agent`` header used for requests (otherwise browser default is used)
- ``browser``:  Either ``chromium``, ``chrome``, ``chrome-beta``, ``msedge``,
  ``msedge-beta``, ``msedge-dev``, ``firefox``, ``webkit`` (must be installed with ``playwright install``)

Because this job uses Playwright_ to
render the page in a headless browser instance, it uses massively more resources
than a "URL" job. Use it only on pages where ``url`` does not return the correct
results. In many cases, instead of using a "Browser" job, you can use the output
of an API called by the page as it loads, which contains the information you are
you're looking for by using the much faster "URL" job type.

(Note: ``navigate`` implies ``kind: browser``)

.. _Playwright: https://playwright.dev/python/


Shell
-----

This job type allows you to watch the output of arbitrary shell commands,
which is useful for e.g. monitoring an FTP uploader folder, output of
scripts that query external devices (RPi GPIO), etc...

.. code-block:: yaml

   name: "What is in my Home Directory?"
   command: "ls -al ~"

Required keys:

- ``command``: The shell command to execute

Job-specific optional keys:

- ``stderr``: Change how standard error is treated, see below

(Note: ``command`` implies ``kind: shell``)

Configuring ``stderr`` behavior for shell jobs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default urlwatch captures ``stderr`` for error reporting (non-zero exit
code), but ignores the output when the shell job exits with exit code 0.

This behavior can be customized using the ``stderr`` key:

- ``ignore``: Capture ``stderr``, report on non-zero exit code, ignore otherwise (default)
- ``urlwatch``: ``stderr`` of the shell job is sent to ``stderr`` of the ``urlwatch`` process;
  any error message on ``stderr`` will not be visible in the error message from the reporter
  (legacy default behavior of urlwatch 2.24 and older)
- ``fail``: Treat the job as failed if there is *any* output on ``stderr``, even with exit status 0
- ``stdout``: Merge ``stderr`` output into ``stdout``, which means stderr output is also considered
  for the change detection/diff part of urlwatch (this is similar to ``2>&1`` in a shell)

For example, this job definition will make the job appear as failed,
even though the script exits with exit code 0:

.. code-block:: yaml

    command: |
      echo "Normal standard output."
      echo "Something goes to stderr, which makes this job fail." 1>&2
      exit 0
    stderr: fail

On the other hand, if you want to diff both stdout and stderr of the job, use this:

.. code-block:: yaml

    command: |
      echo "An important line on stdout."
      echo "Another important line on stderr." 1>&2
    stderr: stdout


Optional keys for all job types
-------------------------------

- ``name``: Human-readable name/label of the job
- ``filter``: :doc:`filters` (if any) to apply to the output (can be tested with ``--test-filter``)
- ``max_tries``: Number of times to retry fetching the resource
- ``diff_tool``: Command to a custom tool for generating diff text
- ``diff_filter``: :doc:`filters` (if any) to apply to the diff result (can be tested with ``--test-diff-filter``)
- ``treat_new_as_changed``: Will treat jobs that don't have any historic data as ``CHANGED`` instead of ``NEW`` (and create a diff for new jobs)
- ``compared_versions``: Number of versions to compare for similarity
- ``kind`` (redundant): Either ``url``, ``shell`` or ``browser``.  Automatically derived from the unique key (``url``, ``command`` or ``navigate``) of the job type
- ``user_visible_url``: Different URL to show in reports (e.g. when watched URL is a REST API URL, and you want to show a webpage)
- ``enabled``: Can be set to false to disable an individual job (default is ``true``)


Setting keys for all jobs at once
---------------------------------

The main :doc:`configuration` file has a ``job_defaults``
key that can be used to configure keys for all jobs at once.

.. only:: man

    See :manpage:`urlwatch-config(5)` for how to configure job defaults.

.. only:: man

    Examples
    --------

    See :manpage:`urlwatch-cookbook(7)` for example job configurations.

    Files
    -----

    ``$XDG_CONFIG_HOME/urlwatch/urls.yaml``

    See also
    --------

    :manpage:`urlwatch(1)`,
    :manpage:`urlwatch-intro(5)`,
    :manpage:`urlwatch-filters(5)`

