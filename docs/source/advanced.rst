.. _advanced_topics:

Advanced Topics
===============

If you want to change some settings for all your jobs, edit the
``job_defaults`` section in your config file:

.. code-block:: yaml

   ...
   job_defaults:
     all:
       diff_tool: wdiff
     url:
       ignore_connection_errors: true

The above config file sets all jobs to use wdiff as diff tool, and all
“url” jobs to ignore connection errors.


Adding URLs from the command line
---------------------------------

Quickly adding new URLs to the job list from the command line::

    urlwatch --add url=http://example.org,name=Example


Using word-based differences
----------------------------

You can also specify an external ``diff``-style tool (a tool that takes
two filenames (old, new) as parameter and returns on its standard output
the difference of the files), for example to use GNU ``wdiff`` to get
word-based differences instead of line-based difference:

.. code-block:: yaml

   url: https://example.com/
   diff_tool: wdiff

Note that ``diff_tool`` specifies an external command-line tool, so that
tool must be installed separately (e.g. ``apt install wdiff`` on Debian
or ``brew install wdiff`` on macOS). Coloring is supported for
``wdiff``-style output, but potentially not for other diff tools.


Ignoring connection errors
--------------------------

In some cases, it might be useful to ignore (temporary) network errors
to avoid notifications being sent. While there is a ``display.error``
config option (defaulting to ``true``) to control reporting of errors
globally, to ignore network errors for specific jobs only, you can use
the ``ignore_connection_errors`` key in the job list configuration file:

.. code-block:: yaml

   url: https://example.com/
   ignore_connection_errors: true

Similarly, you might want to ignore some (temporary) HTTP errors on the
server side:

.. code-block:: yaml

   url: https://example.com/
   ignore_http_error_codes: 408, 429, 500, 502, 503, 504

or ignore all HTTP errors if you like:

.. code-block:: yaml

   url: https://example.com/
   ignore_http_error_codes: 4xx, 5xx


Overriding the content encoding
-------------------------------

For web pages with misconfigured HTTP headers or rare encodings, it may
be useful to explicitly specify an encoding from Python’s `Standard
Encodings <https://docs.python.org/3/library/codecs.html#standard-encodings>`__.

.. code-block:: yaml

   url: https://example.com/
   encoding: utf-8


Changing the default timeout
----------------------------

By default, url jobs timeout after 60 seconds. If you want a different
timeout period, use the ``timeout`` key to specify it in number of
seconds, or set it to 0 to never timeout.

.. code-block:: yaml

   url: https://example.com/
   timeout: 300


Supplying cookie data
---------------------

It is possible to add cookies to HTTP requests for pages that need it,
the YAML syntax for this is:

.. code-block:: yaml

   url: http://example.com/
   cookies:
       Key: ValueForKey
       OtherKey: OtherValue


Comparing with several latest snapshots
---------------------------------------

If a webpage frequently changes between several known stable states, it
may be desirable to have changes reported only if the webpage changes
into a new unknown state. You can use ``compared_versions`` to do this.

.. code-block:: yaml

   url: https://example.com/
   compared_versions: 3

In this example, changes are only reported if the webpage becomes
different from the latest three distinct states. The differences are
shown relative to the closest match.


Receving a report every time urlwatch runs
------------------------------------------
If you are watching pages that change seldomly, but you still want to
be notified daily if ``urlwatch`` still works, you can watch the output
of the ``date`` command, for example:

.. code-block:: yaml

   name: "urlwatch watchdog"
   command: "date"

Since the output of ``date`` changes every second, this job should produce a
report every time urlwatch is run.


Using Redis as a cache backend
------------------------------------------
If you want to use Redis as a cache backend over the default SQLite3 file::

    urlwatch --cache=redis://localhost:6379/

There is no migration path from the SQLite3 format, the cache will be empty
the first time Redis is used.


Watching changes on .onion (Tor) pages
--------------------------------------

Since pages on the `Tor Network`_ are not accessible via public DNS and TCP,
you need to either configure a Tor client as HTTP/HTTPS proxy or use the
``torify(1)`` tool from the ``tor`` package (``apt install tor`` on Debian,
``brew install tor`` on macOS). Setting up Tor is out of scope for this
document. On a properly set up Tor installation, one can just prefix the
``urlwatch`` command with the ``torify`` wrapper to access .onion pages:

.. code-block:: bash

   torify urlwatch

.. _Tor Network: https://www.torproject.org


Watching Facebook Page Events
-----------------------------

If you want to be notified of new events on a public Facebook page, you
can use the following job pattern, replace ``PAGE`` with the name of the
page (can be found by navigating to the events page on your browser):

.. code-block:: yaml

   url: https://m.facebook.com/PAGE/pages/permalink/?view_type=tab_events
   filter:
     - css:
         selector: div#objects_container
         exclude: 'div.x, #m_more_friends_who_like_this, img'
     - re.sub:
         pattern: '(/events/\d*)[^"]*'
         repl: '\1'
     - html2text: pyhtml2text
   comparison_filter: additions

