.. _filters:

.. All code examples here should have a unique URL that maps to
   an entry in test/data/filter_documentation_testdata.yaml which
   will be used to provide input/output data for the filter example
   so that the examples can be verified to be correct automatically.

Filters
=======

Filters are currently used in two stages of processing:

* Applied to the downloaded page before diffing the changes (``filter``)
* Applied to the diff result before reporting the changes (``diff_filter``)

While creating your filter pipeline, you might want to preview what the
filtered output looks like. You can do so by first configuring your job
and then running urlwatch with the ``--test-filter`` command, passing in
the index (from ``--list``) or the URL/location of the job to be tested:

::

   urlwatch --test-filter 1   # Test the first job in the list
   urlwatch --test-filter https://example.net/  # Test the job with the given URL

The output of this command will be the filtered plaintext of the job,
this is the output that will (in a real urlwatch run) be the input to
the diff algorithm.

The ``filter`` is only applied to new content, the old content was
already filtered when it was retrieved. This means that changes to
``filter`` are not visible when reporting unchanged contents
(see :ref:`configuration_display` for details), and the diff output
will be between (old content with filter at the time old content was
retrieved) and (new content with current filter).


Built-in filters
----------------

The list of built-in filters can be retrieved using::

    urlwatch --features

At the moment, the following filters are built-in:

- **beautify**: Beautify HTML
- **css**: Filter XML/HTML using CSS selectors
- **element-by-class**: Get all HTML elements by class
- **element-by-id**: Get an HTML element by its ID
- **element-by-style**: Get all HTML elements by style
- **element-by-tag**: Get an HTML element by its tag
- **format-json**: Convert to formatted json
- **grep**: Filter only lines matching a regular expression
- **grepi**: Remove lines matching a regular expression
- **hexdump**: Convert binary data to hex dump format
- **html2text**: Convert HTML to plaintext
- **pdf2text**: Convert PDF to plaintext
- **ical2text**: Convert `iCalendar`_ to plaintext
- **re.sub**: Replace text with regular expressions using Python's re.sub
- **reverse**: Reverse input items
- **sha1sum**: Calculate the SHA-1 checksum of the content
- **shellpipe**: Filter using a shell command
- **sort**: Sort input items
- **strip**: Strip leading and trailing whitespace
- **xpath**: Filter XML/HTML using XPath expressions

.. To convert the "urlwatch --features" output, use:
   sed -e 's/^  \* \(.*\) - \(.*\)$/- **\1**: \2/'

.. _iCalendar: https://en.wikipedia.org/wiki/ICalendar


Picking out elements from a webpage
-----------------------------------

You can pick only a given HTML element with the built-in filter, for
example to extract ``<div id="something">.../<div>`` from a page, you
can use the following in your ``urls.yaml``:

.. code:: yaml

   url: http://example.org/idtest.html
   filter:
     - element-by-id: something

Also, you can chain filters, so you can run html2text on the result:

.. code:: yaml

   url: http://example.net/id2text.html
   filter:
     - element-by-id: something
     - html2text


Chaining multiple filters
-------------------------

The example urls.yaml file also demonstrates the use of built-in
filters, here 3 filters are used: html2text, line-grep and whitespace
removal to get just a certain info field from a webpage:

.. code:: yaml

   url: https://example.net/version.html
   filter:
     - html2text
     - grep: "Current.*version"
     - strip


Extracting only the ``<body>`` tag of a page
--------------------------------------------

If you want to extract only the body tag you can use this filter:

.. code:: yaml

   url: https://example.org/bodytag.html
   filter:
     - element-by-tag: body


Filtering based on an XPath expression
--------------------------------------

To filter based on an
`XPath <https://www.w3.org/TR/1999/REC-xpath-19991116/>`__ expression,
you can use the ``xpath`` filter like so (see Microsoft’s `XPath
Examples <https://msdn.microsoft.com/en-us/library/ms256086(v=vs.110).aspx>`__
page for some other examples):

.. code:: yaml

   url: https://example.net/xpath.html
   filter:
     - xpath: /html/body/marquee

This filters only the ``<marquee>`` elements directly below the ``<body>``
element, which in turn must be below the ``<html>`` element of the document,
stripping out everything else.


Filtering based on CSS selectors
--------------------------------

To filter based on a `CSS
selector <https://www.w3.org/TR/2011/REC-css3-selectors-20110929/>`__,
you can use the ``css`` filter like so:

.. code:: yaml

   url: https://example.net/css.html
   filter:
     - css: ul#groceries > li.unchecked

This would filter only ``<li class="unchecked">`` tags directly
below ``<ul id="groceries">`` elements.

Some limitations and extensions exist as explained in `cssselect’s
documentation <https://cssselect.readthedocs.io/en/latest/#supported-selectors>`__.


Using XPath and CSS filters with XML and exclusions
---------------------------------------------------

By default, XPath and CSS filters are set up for HTML documents.
However, it is possible to use them for XML documents as well (these
examples parse an RSS feed and filter only the titles and publication
dates):

.. code:: yaml

   url: https://example.com/blog/xpath-index.rss
   filter:
     - xpath:
         path: '//item/title/text()|//item/pubDate/text()'
         method: xml

.. code:: yaml

   url: http://example.com/blog/css-index.rss
   filter:
     - css:
         selector: 'item > title, item > pubDate'
         method: xml
     - html2text: re

To match an element in an `XML
namespace <https://www.w3.org/TR/xml-names/>`__, use a namespace prefix
before the tag name. Use a ``:`` to seperate the namespace prefix and
the tag name in an XPath expression, and use a ``|`` in a CSS selector.

.. code:: yaml

   url: https://example.net/feed/xpath-namespace.xml
   filter:
     - xpath:
         path: '//item/media:keywords/text()'
         method: xml
         namespaces:
           media: http://search.yahoo.com/mrss/

.. code:: yaml

   url: http://example.org/feed/css-namespace.xml
   filter:
     - css:
         selector: 'item > media|keywords'
         method: xml
         namespaces:
           media: http://search.yahoo.com/mrss/
     - html2text

Alternatively, use the XPath expression ``//*[name()='<tag_name>']`` to
bypass the namespace entirely.

Another useful option with XPath and CSS filters is ``exclude``.
Elements selected by this ``exclude`` expression are removed from the
final result. For example, the following job will not have any ``<a>``
tag in its results:

.. code:: yaml

   url: https://example.org/css-exclude.html
   filter:
     - css:
         selector: body
         exclude: a


Filtering PDF documents
-----------------------

To monitor the text of a PDF file, you use the `pdf2text` filter. It requires 
the installation of the `pdftotext`_ library and any of its
`OS-specific dependencies`_.

.. _pdftotext: https://github.com/jalan/pdftotext/blob/master/README.md#pdftotext
.. _OS-specific dependencies: https://github.com/jalan/pdftotext/blob/master/README.md#os-dependencies

This filter *must* be the first filter in a chain of filters, since it
consumes binary data and outputs text data.

.. code-block:: yaml

   url: https://example.net/pdf-test.pdf
   filter:
     - pdf2text
     - strip


If the PDF file is password protected, you can specify its password:

.. code-block:: yaml

   url: https://example.net/pdf-test-password.pdf
   filter:
     - pdf2text:
         password: urlwatchsecret
     - strip


Sorting of webpage content
--------------------------

Sometimes a web page can have the same data between comparisons but it
appears in random order. If that happens, you can choose to sort before
the comparison.

.. code:: yaml

   url: https://example.net/sorting.txt
   filter:
     - sort

The sort filter takes an optional ``separator`` parameter that defines
the item separator (by default sorting is line-based), for example to
sort text paragraphs (text separated by an empty line):

.. code:: yaml

   url: http://example.org/paragraphs.txt
   filter:
     - sort:
         separator: "\n\n"

This can be combined with a boolean ``reverse`` option, which is useful
for sorting and reversing with the same separator (using ``%`` as
separator, this would turn ``3%2%4%1`` into ``4%3%2%1``):

.. code:: yaml

   url: http://example.org/sort-reverse-percent.txt
   filter:
     - sort:
         separator: '%'
         reverse: true


Reversing of lines or separated items
-------------------------------------

To reverse the order of items without sorting, the ``reverse`` filter
can be used. By default it reverses lines:

.. code:: yaml

   url: http://example.com/reverse-lines.txt
   filter:
     - reverse

This behavior can be changed by using an optional separator string
argument (e.g. items separated by a pipe (``|``) symbol,
as in ``1|4|2|3``, which would be reversed to ``3|2|4|1``):

.. code:: yaml

   url: http://example.net/reverse-separator.txt
   filter:
     - reverse: '|'

Alternatively, the filter can be specified more verbose with a dict.
In this example ``"\n\n"`` is used to separate paragraphs (items that
are separated by an empty line):

.. code:: yaml

   url: http://example.org/reverse-paragraphs.txt
   filter:
     - reverse:
         separator: "\n\n"


Watching Github releases
------------------------

This is an example how to watch the GitHub “releases” page for a given
project for the latest release version, to be notified of new releases:

.. code:: yaml

   url: https://github.com/thp/urlwatch/releases
   filter:
     - xpath: '(//div[contains(@class,"release-timeline-tags")]//h4)[1]/a'
     - html2text: re
     - strip


Remove or replace text using regular expressions
------------------------------------------------

Just like Python’s ``re.sub`` function, there’s the possibility to apply
a regular expression and either remove of replace the matched text. The
following example applies the filter 3 times:

1. Just specifying a string as the value will replace the matches with
   the empty string.
2. Simple patterns can be replaced with another string using “pattern”
   as the expression and “repl” as the replacement.
3. You can use groups (``()``) and back-reference them with ``\1``
   (etc..) to put groups into the replacement string.

All features are described in Python’s
`re.sub <https://docs.python.org/3/library/re.html#re.sub>`__
documentation (the ``pattern`` and ``repl`` values are passed to this
function as-is, with the value of ``repl`` defaulting to the empty
string).

.. code:: yaml

   url: https://example.com/regex-substitute.html
   filter:
       - re.sub: '\s*href="[^"]*"'
       - re.sub:
           pattern: '<h1>'
           repl: 'HEADING 1: '
       - re.sub:
           pattern: '</([^>]*)>'
           repl: '<END OF TAG \1>'


Using a shell script as a filter
--------------------------------

While the built-in filters are powerful for processing markup such as
HTML and XML, in some cases you might already know how you would filter
your content using a shell command or shell script. The ``shellpipe``
filter allows you to start a shell and run custom commands to filter
the content.

The text data to be filtered will be written to the standard input
(``stdin``) of the shell process and the filter output will be taken
from the shell's standard output (``stdout``).

For example, if you want to use ``grep`` tool with the case insensitive
matching option (``-i``) and printing only the matching part of
the line (``-o``), you can specify this as ``shellpipe`` filter:

.. code:: yaml

   url: https://example.net/shellpipe-grep.txt
   filter:
     - shellpipe: "grep -i -o 'price: <span>.*</span>'"

This feature also allows you to use ``sed``, ``awk`` and ``perl``
one-liners for text processing (of course, any text tool that
works in a shell can be used). For example, this ``awk`` one-liner
prepends the line number to each line:

.. code:: yaml

   url: https://example.net/shellpipe-awk-oneliner.txt
   filter:
     - shellpipe: awk '{ print FNR " " $0 }'

You can also use a multi-line command for a more sophisticated
shell script (``|`` in YAML denotes the start of a text block):

.. code:: yaml

   url: https://example.org/shellpipe-multiline.txt
   filter:
     - shellpipe: |
         FILENAME=`mktemp`
         # Copy the input to a temporary file, then pipe through awk
         tee $FILENAME | awk '/The numbers for (.*) are:/,/The next draw is on (.*)./'
         # Analyze the input file in some other way
         echo "Input lines: $(wc -l $FILENAME | awk '{ print $1 }')"
         rm -f $FILENAME


Within the ``shellpipe`` script, two environment variables will
be set for further customization (this can be useful if you have
a external shell script file that is used as filter for multiple
jobs, but needs to treat each job in a slightly different way):

+----------------------------+------------------------------------------------------+
| Environment variable       | Contents                                             |
+============================+======================================================+
| ``$URLWATCH_JOB_NAME``     | The name of the job (``name`` key in jobs YAML)      |
+----------------------------+------------------------------------------------------+
| ``$URLWATCH_JOB_LOCATION`` | The URL of the job, or command line (for shell jobs) |
+----------------------------+------------------------------------------------------+
