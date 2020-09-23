.. _jobs:

Jobs
====

Jobs are the kind of things that `urlwatch` can monitor.

The list of jobs to run are contained in the configuration file ``urls.yaml``,
accessed with the command ``urlwatch --edit``, each separated by a line
containing only ``---``.

While optional, it is recommended that each job starts with a ``name`` entry:

.. code-block:: yaml

    name: "This is a human-readable name/label of the job"


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
- ``http_proxy``: Proxy server to use for HTTP requests
- ``https_proxy``: Proxy server to use for HTTPS requests
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

This job type is a resource-intensive variant of "URL" to handle web pages
requiring JavaScript in order to render the content to be monitored.

The optional ``pyppeteer`` package must be installed to run "Browser" jobs
(see :ref:`dependencies`).

At the moment, the Chromium version used by ``pyppeteer`` only supports
macOS (x86_64), Windows (both x86 and x64) and Linux (x86_64). See
`this issue <https://github.com/pyppeteer/pyppeteer/issues/155>`__ in the
Pyppeteer issue tracker for progress on getting ARM devices supported
(e.g. Raspberry Pi).

Because ``pyppeteer`` downloads a special version of Chromium (~ 100 MiB),
the first execution of a ``browser`` job could take some time (and bandwidth).
It is possible to run ``pyppeteer-install`` to pre-download Chromium.

.. code-block:: yaml

   name: "A page with JavaScript"
   navigate: "https://example.org/"

Required keys:

- ``navigate``: URL to navigate to with the browser

Job-specific optional keys:

- ``wait_until``:  Either ``load``, ``domcontentloaded``, ``networkidle0``, or ``networkidle2`` (see :ref:`advanced_topics`)


As this job uses `Pyppeteer <https://github.com/pyppeteer/pyppeteer>`__
to render the page in a headless Chromium instance, it requires massively
more resources than a "URL" job. Use it only on pages where ``url`` does not
give the right results.

Hint: in many instances instead of using a "Browser" job you can
monitor the output of an API called by the site during page loading
containing the information you're after using the much faster "URL" job type.

(Note: ``navigate`` implies ``kind: browser``)


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

- none

(Note: ``command`` implies ``kind: shell``)


Optional keys for all job types
-------------------------------

- ``name``: Human-readable name/label of the job
- ``filter``: :ref:`filters` (if any) to apply to the output (can be tested with ``--test-filter``)
- ``max_tries``: Number of times to retry fetching the resource
- ``diff_tool``: Command to a custom tool for generating diff text
- ``diff_filter``: :ref:`filters` (if any) to apply to the diff result (can be tested with ``--test-diff-filter``)
- ``compared_versions``: Number of versions to compare for similarity
- ``kind`` (redundant): Either ``url``, ``shell`` or ``browser``.  Automatically derived from the unique key (``url``, ``command`` or ``navigate``) of the job type


Settings keys for all jobs at once
----------------------------------

See :ref:`job_defaults` for how to configure keys for all jobs at once.
