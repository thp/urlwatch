.. _advanced_topics:

Advanced Topics
===============


Adding URLs from the command line
---------------------------------

Quickly adding new URLs to the job list from the command line::

    urlwatch --add url=http://example.org,name=Example


Using word-based differences
----------------------------

You can also specify an external ``diff``-style tool (a tool that takes
two filenames (old, new) as parameter and returns on its standard output
the difference of the files), for example to use :manpage:`wdiff(1)` to get
word-based differences instead of line-based difference:

.. code-block:: yaml

   url: https://example.com/
   diff_tool: wdiff

Note that ``diff_tool`` specifies an external command-line tool, so that
tool must be installed separately (e.g. ``apt install wdiff`` on Debian
or ``brew install wdiff`` on macOS). Coloring is supported for
``wdiff``-style output, but potentially not for other diff tools.


Ignoring whitespace changes
---------------------------

If you would like to ignore whitespace changes so that you don't receive
notifications for trivial differences, you can use ``diff_tool`` for this.
For example:

.. code-block:: yaml

   diff_tool: "diff --ignore-all-space -u"

To use a different external ``diff``-like tool, make sure it returns unified
output format for best results.


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


Receiving a report every time urlwatch runs
-------------------------------------------

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
:manpage:`torify(1)` tool from the ``tor`` package (``apt install tor`` on Debian,
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

   url: http://m.facebook.com/PAGE/pages/permalink/?view_type=tab_events
   filter:
     - css:
         selector: div#objects_container
         exclude: 'div.x, #m_more_friends_who_like_this, img'
     - re.sub:
         pattern: '(/events/\d*)[^"]*'
         repl: '\1'
     - html2text: pyhtml2text


Only show added or removed lines
--------------------------------

The ``diff_filter`` feature can be used to filter the diff output text
with the same tools (see :doc:`filters`) used for filtering web pages.

In order to show only diff lines with added lines, use:

.. code-block:: yaml

   url: http://example.com/things-get-added.html
   diff_filter:
     - grep: '^[@+]'

This will only keep diff lines starting with ``@`` or ``+``. Similarly,
to only keep removed lines:

.. code-block:: yaml

   url: http://example.com/things-get-removed.html
   diff_filter:
     - grep: '^[@-]'

More sophisticated diff filtering is possibly by combining existing
filters, writing a new filter or using ``shellpipe`` to delegate the
filtering/processing of the diff output to an external tool.

Read the next section if you want to disable empty notifications.


Disable empty notifications
---------------------------

As an extension to the previous example, let's say you want to only
get notified with all lines added, but receive no notifications at all
if lines are removed.

A diff usually looks like this:

.. code-block::

    --- @	Fri, 04 Mar 2022 19:58:14 +0100
    +++ @	Fri, 04 Mar 2022 19:58:22 +0100
    @@ -1,3 +1,3 @@
     someline
    -someotherlines
    +someotherline
     anotherline

We want to filter all lines starting with "+" only, but because of
the headers we also want to filter lines that start with "+++",
which can be accomplished like so:

.. code-block:: yaml

    url: http://example.com/only-added.html
    diff_filter:
      - grep: '^[+]'      # Include all lines starting with "+"
      - grepi: '^[+]{3}'  # Exclude the line starting with "+++"

This deals with all diff lines now, but since urlwatch reports
"changed" pages even when the ``diff_filter`` returns an empty string
(which might be useful in some cases), you have to explicitly opt out
by using ``urlwatch --edit-config`` and setting the ``empty-diff``
option to ``false`` in the ``display`` category:

.. code-block:: yaml

    display:
      empty-diff: false


Pass diff output to a custom script
-----------------------------------

In some situations, it might be useful to run a script with the diff as input
when changes were detected (e.g. to start an update or process something). This
can be done by combining ``diff_filter`` with the ``shellpipe`` filter, which
can be any custom script.

The output of the custom script will then be the diff result as reported by
urlwatch, so if it outputs any status, the ``CHANGED`` notification that
urlwatch does will contain the output of the custom script, not the original
diff. This can even have a "normal" filter attached to only watch links
(the ``css: a`` part of the filter definitions):

.. code-block:: yaml

   url: http://example.org/downloadlist.html
   filter:
     - css: a
   diff_filter:
     - shellpipe: /usr/local/bin/process_new_links.sh


Setting the content width for ``html2text`` (``lynx`` method)
-------------------------------------------------------------

When using the ``lynx`` method in the ``html2text`` filter, it uses a default
width that will cause additional line breaks to be inserted.

To set the ``lynx`` output width to 400 characters, use this filter setup:

.. code-block:: yaml

   url: http://example.com/longlines.html
   filter:
     - html2text:
         method: lynx
         width: 400


Comparing web pages visually
----------------------------

To compare the visual contents of web pages, Nicolai has written
`pyvisualcompare <https://github.com/nspo/pyvisualcompare>`__ as
a frontend (with GUI) to ``urlwatch``. The tool can be used to
select a region of a web page. It then generates a configuration
for ``urlwatch`` to run ``pyvisualcompare`` and generate a hash
for the screen contents.


Configuring how long browser jobs wait for pages to load
--------------------------------------------------------

For browser jobs, you can configure how long the headless browser will wait
before a page is considered loaded by using the `wait_until` option. It can take one of four values:

  - `load` will wait until the `load` browser event is fired (default).
  - `documentloaded` will wait until the `DOMContentLoaded` browser event is fired.
  - `networkidle0` will wait until there are no more than 0 network connections for at least 500 ms.
  - `networkidle2` will wait until there are no more than 2 network connections for at least 500 ms.


Treating ``NEW`` jobs as ``CHANGED``
------------------------------------

In some cases (e.g. when the ``diff_tool`` or ``diff_filter`` executes some
external command as a side effect that should also run for the initial page
state), you can set the ``treat_new_as_changed`` to ``true``, which will make
the job report as ``CHANGED`` instead of ``NEW`` the first time it is retrieved
(and the diff will be reported, too).

.. code-block:: yaml

   url: http://example.com/initialpage.html
   treat_new_as_changed: true

This option will also change the behavior of ``--test-diff-filter``, and allow
testing the diff filter if only a single version of the page has been
retrieved.


Monitoring the same URL in multiple jobs
----------------------------------------

Because urlwatch uses the ``url``/``navigate`` (for URL/Browser jobs) and/or
the ``command`` (for Shell jobs) key as unique identifier, each URL can only
appear in a single job. If you want to monitor the same URL multiple times,
you can append ``#1``, ``#2``, ... (or anything that makes them unique) to
the URLs, like this:

.. code-block:: yaml

    name: "Looking for Thing A"
    url: http://example.com/#1
    filter:
      - grep: "Thing A"
    ---
    name: "Looking for Thing B"
    url: http://example.com/#2
    filter:
      - grep: "Thing B"


Running a subset of jobs
------------------------

To run one or more specific jobs instead of all known jobs, provide
the job index numbers to the urlwatch command. For example, to run
jobs with index 2, 4, and 7:

.. code-block:: bash

   urlwatch 2 4 7


Sending HTML form data using POST
---------------------------------

To simulate submitting a HTML form using the POST method, you can pass
the form fields in the ``data`` field of the job description:

.. code-block:: yaml

    name: "My POST Job"
    url: http://example.com/foo
    data:
      username: "foo"
      password: "bar"
      submit: "Send query"

By default, the request will use the HTTP ``POST`` method, and the
``Content-type`` will be set to ``application/x-www-form-urlencoded``.


Sending arbitrary data using HTTP PUT
-------------------------------------

It is possible to customize the HTTP method and ``Content-type`` header,
allowing you to send arbitrary requests to the server:

.. code-block:: yaml

    name: "My PUT Request"
    url: http://example.com/item/new
    method: PUT
    headers:
      Content-type: application/json
    data: '{"foo": true}'

.. only:: man

    See also
    --------

    :manpage:`urlwatch(1)`,
    :manpage:`urlwatch-intro(7)`,
    :manpage:`urlwatch-jobs(5)`,
    :manpage:`urlwatch-filters(5)`,
    :manpage:`urlwatch-config(5)`,
    :manpage:`urlwatch-reporters(5)`

