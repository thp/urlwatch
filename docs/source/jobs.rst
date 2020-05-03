Jobs
====

Jobs are the kind of things that urlwatch can monitor. The most-used
job type is ``url`` for watching web pages without dynamic HTML.

Optional keys for all jobs:

- ``kind``: Either ``url``, ``shell`` or ``browser``; for the built-in
  jobs, this is usually auto-detected and can be left out, because the
  job kind can be derived from the unique key (``url``, ``command`` or
  ``navigate``) that the job has
- ``name``: Human-readable name/label of the job
- ``filter``: Which filters (if any) to apply to the output
- ``max_tries``: How often to retry fetching the resource
- ``diff_tool``: Custom tool for generating diff text
- ``compared_versions``: Number of versions to compare for similarity

The configuration file ``urls.yaml`` contains a list of jobs to run.


URL
---

This is the main job type -- it retrieves a document from a web server::

    kind: url
    name: "urlwatch webpage"
    url: "https://thp.io/2008/urlwatch/"

Required keys:

- ``url``: The URL to the document to watch for changes

Optional keys:

- ``cookies``: Cookies to send with the request
- ``data``: HTTP POST/PUT data
- ``method``: HTTP method to use (default: ``GET``)
- ``ssl_no_verify``: Do not verify SSL certificates
- ``ignore_cached``: Do not use cache control (ETag/Last-Modified) values
- ``http_proxy``: Proxy server to use for HTTP requests
- ``https_proxy``: Proxy server to use for HTTPS requests
- ``headers``: HTTP header to send along with the request
- ``encoding``: Override the character encoding from the server
- ``timeout``: Override the default socket timeout
- ``ignore_connection_errors``: Ignore (temporary) connection errors
- ``ignore_http_error_codes``: List of HTTP errors to ignore
- ``ignore_timeout_errors``: Do not report errors when the timeout is hit
- ``ignore_too_many_redirects``: Ignore redirect loops


Shell
-----

This job allows you to watch the output of arbitrary shell commands,
which is useful for e.g. monitoring a FTP uploader folder, output of
scripts that query external devices (RPi GPIO), etc...

Required keys:

- ``command``: The shell command to execute

Here is a simple example job:

.. code:: yaml

   kind: shell
   name: "What is in my Home Directory?"
   command: "ls -al ~"

If you are watching pages that change seldomly, but you still want to
be notified daily if ``urlwatch`` still works, you can watch the output
of the ``date`` command, for example:

.. code:: yaml

   kind: shell
   name: "Daily urlwatch watchdog"
   command: "date +%F"

Since the output of ``date +%F`` (YYYY-MM-DD) changes every day, this
job should produce a diff / report every day.


Browser
-------

This is an advanced variant of the "URL" job and uses a headless
web browser instance to run client-side JavaScript and handle more
dynamic web pages.

Required keys:

- ``navigate``: URL to navigate to with the browser

If the webpage you are trying to watch runs client-side JavaScript to
render the page, `Requests-HTML <http://html.python-requests.org>`__ can
now be used to render the page in a headless Chromium instance first and
then use the HTML of the resulting page.

Use the ``browser`` kind in the configuration and the ``navigate`` key
to set the URL to retrieve. note that the normal ``url`` job keys are
not supported for the ``browser`` job types at the moment, for example:

.. code:: yaml

   kind: browser
   name: "A Page With JavaScript"
   navigate: http://example.org/

The "browser" job does not support all the custom options that the "url"
job supports. Also, it requires more resources (it starts up a whole
headless browser instance), so only use it on pages where the "url" job
does not give the right results. For some pages, instead of watching the
"frontend" HTML page, watching a JSON URL from the API backend can do
the trick without having to resort to running client-side JavaScript.
