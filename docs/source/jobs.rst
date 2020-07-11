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


Navigate
--------

This job type is a resource-intensive variant of "URL" to handle web pages
requiring JavaScript in order to render the content to be monitored.

The optional ``requests-html`` package must be installed to run "Navigate" jobs
(see :ref:`dependencies`).

.. code-block:: yaml

   name: "A page with JavaScript"
   navigate: "https://example.org/"

Required keys:

- ``navigate``: URL to navigate to with the browser

Job-specific optional keys:

- none

As this job uses `Requests-HTML <http://html.python-requests.org>`__
to render the page in a headless Chromium instance, it requires massively
more resources than a "URL" job. Use it only on pages where ``url`` does not
give the right results.

Hint: in many instances instead of using "Navigate" you can 
monitor the output of an API called by the site during page loading
containing the information you're after using the much faster "URL" job type.

(Note: ``navigate`` implies ``kind: browser``)


Command
-------

This job type allows you to watch the output of arbitrary shell commands,
which is useful for e.g. monitoring a FTP uploader folder, output of
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
- :ref:`comparison_filter`: fiter unified diff output to keep only addition lines or deleted lines
- ``name``: Human-readable name/label of the job
- ``filter``: :ref:`filters` (if any) to apply to the output
- ``max_tries``: Number of times to retry fetching the resource
- ``diff_tool``: Command to a custom tool for generating diff text
- ``compared_versions``: Number of versions to compare for similarity
- ``kind`` (redundant): Either ``url``, ``shell`` or ``browser``.  Automatically derived from the unique key (``url``, ``command`` or ``navigate``) of the job type


.. _comparison_filter:

``comparison_filter``
^^^^^^^^^^^^^^^^^^^^^

The ``comparison_filter`` filters the output of the unified diff to keep only addition or deleted lines
 - A value of `additions` will cause reports to contain only lines that are added by the diff (no deletions).
 - A value of `deleted` key will cause reports to contain only lines that are deleted by the diff (no additions).

`comparison_filter: additions` is extremely useful for monitoring new content on sites where content gets added while old content "scrolls" away.

Because lines that are modified generate both a deleted and an added line by the diff, this filters always displays modified lines.

As a safeguard, `additions` will warn when 75% of more of the change consists of deletions.


Sample output for `additions`:

.. code-block:: none

   ---------------------------------------------------------------------------
   CHANGED: https://example.com
   ---------------------------------------------------------------------------
   ... @   Sat, 23 May 2020 00:00:00 +0000
   +++ @   Sat, 23 May 2020 01:00:00 +0000
   -**Comparison type: Additions only**
   @@ -1,2 +1,2 @@
   +This is a line that has been added or changed

Sample output for `deletions`:

.. code-block:: none

   ---------------------------------------------------------------------------
   CHANGED: https://example.com
   ---------------------------------------------------------------------------
   --- @   Sat, 23 May 2020 00:00:00 +0000
   ... @   Sat, 23 May 2020 01:00:00 +0000
   +**Comparison type: Deletions only**
   @@ -1,2 +1,2 @@
   -This is a line that has been deleted or changed

Sample output for `additions` when the 75% deletions safeguard is triggered:

.. code-block:: none

   ---------------------------------------------------------------------------
   CHANGED: https://example.com
   ---------------------------------------------------------------------------
   ... @   Sat, 23 May 2020 00:00:00 +0000
   +++ @   Sat, 23 May 2020 01:00:00 +0000
   -**Comparison type: Additions only**
   .** No additions (only deletions)
   --- WARNING: 39 lines deleted; suggest checking source
   ---------------------------------------------------------------------------


Workaround: due to legacy logic in urlwatch, we are unable to suppress reporting when all changes are filtered out, so a message is added instead:

.. code-block:: none


   ---------------------------------------------------------------------------
   CHANGED: https://example.com
   ---------------------------------------------------------------------------
   ... @   Sat, 23 May 2020 00:00:00 +0000
   +++ @   Sat, 23 May 2020 01:00:00 +0000
   -**Comparison type: Additions only**
   .** No additions (only deletions)
   ---------------------------------------------------------------------------

