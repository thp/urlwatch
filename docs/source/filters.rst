.. _filters:

Filters
=======

Filters are applied to the data downloaded to transform it before the 
end result is compared with the previous version, i.e. "diffing".

Tip: you can try filters by saving your job configuration and running
`urlwatch` with the ``--test-filter`` command, passing in the index (from 
``--list``) or the URL/location of the job to be tested:

.. code-block:: bash

   urlwatch --test-filter 1   # Test the first job in the list
   urlwatch --test-filter https://example.net/  # Test the first job with the given URL

The output of this command will be the text fed to the diff algorithm when you
run `urlwatch`.

The list of built-in filters can be retrieved using::

    urlwatch --features

.. To convert the "urlwatch --features" output, use:
   sed -e 's/^  \* \(.*\) - \(.*\)$/- **\1**: \2/'

.. _iCalendar: https://en.wikipedia.org/wiki/ICalendar


The following filters are available:

To select HTML (or XML) elements:

- :ref:`css <css-and-xpath>`: Filter XML/HTML using CSS selectors
- :ref:`xpath <css-and-xpath>`: Filter XML/HTML using XPath expressions
- :ref:`element-by-class <element-by->`: Get all HTML elements by class
- :ref:`element-by-id <element-by->`: Get an HTML element by its ID
- :ref:`element-by-style <element-by->`: Get all HTML elements by style
- :ref:`element-by-tag <element-by->`: Get an HTML element by its tag

To make HTML more readable:

- :ref:`html2text`: Convert HTML to plaintext
- :ref:`beautify`: Beautify HTML

To make PDFs readable:

- :ref:`pdf2text`: Convert PDF to plaintext

To make JSON more readable:

- :ref:`format-json`: Reformat (pretty-print) JSON

To make iCal more readable:

- :ref:`ical2text`: Convert iCalendar to plaintext

To make binary readable:

- :ref:`hexdump`: Display data in hex dump format

To just detect changes:

- :ref:`sha1sum`: Calculate the SHA-1 checksum of the data

To edit/filter text:

- :ref:`grep`: Keep only lines matching a regular expression
- :ref:`grepi`: Delete lines matching a regular expression
- :ref:`re.sub`: Replace or remove text matching a regular expression
- :ref:`strip`: Strip leading and trailing whitespace
- :ref:`sort`: Sort lines



.. _css-and-xpath:

``css`` and ``xpath``
---------------------

The ``css`` filter extracts content based on a `CSS selector 
<https://www.w3.org/TR/selectors/>`__,. It uses the `cssselect 
<https://pypi.org/project/cssselect/>`__ Python package, which 
has limitations and extensions as explained in its `documentation 
<https://cssselect.readthedocs.io/en/latest/#supported-selectors>`__.

The ``xpath`` filter extracts content based on a `XPath 
<https://www.w3.org/TR/xpath>`__ expression.

Examples: to filter only the ``<body>`` element of the HTML document, stripping
out everything else:

.. code-block:: yaml

   url: https://example.net/
   filter:
     - css: body

.. code-block:: yaml

   url: https://example.net/
   filter: 
     - xpath: '/body'

**Optional keys**
"""""""""""""""""

* ``selector``
* ``path``
* ``method``: either of ``html`` (default) or ``xml``
* ``exclude`` 
* ``namespaces``

Using CSS and XPath filters with XML and exclusions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, CSS and XPath filters are set up for HTML documents, but it is 
possible to use them for XML documents as well.

Example to parse an RSS feed and filter only the titles and publication dates:

.. code-block:: yaml

   url: 'https://heronebag.com/blog/index.xml'
   filter:
     - css:
         method: xml
         selector: 'item > title, item > pubDate'
     - html2text: re

.. code-block:: yaml

   url: 'https://heronebag.com/blog/index.xml'
   filter:
     - xpath:
         method: xml
         path: '//item/title/text()|//item/pubDate/text()'

To match an element in an `XML namespace 
<https://www.w3.org/TR/xml-names/>`__, use a namespace prefix
before the tag name. Use a ``|`` to seperate the namespace prefix and
the tag name in a CSS selector, and use a ``:`` in an XPath expression.

.. code-block:: yaml

   url: 'https://www.wired.com/feed/rss'
   filter:
     - css:
         method: xml
         selector: 'item > media|keywords'
         namespaces:
           media: 'http://search.yahoo.com/mrss/'

.. code-block:: yaml

   url: 'https://www.wired.com/feed/rss'
   filter:
     - xpath:
         method: xml
         path: '//item/media:keywords'
         namespaces:
           media: 'http://search.yahoo.com/mrss/'


Alternatively, use the XPath expression ``//*[name()='<tag_name>']`` to
bypass the namespace entirely.

Another useful option with XPath and CSS filters is ``exclude``.
Elements selected by this ``exclude`` expression are removed from the
final result. For example, the following job will not have any ``<a>``
tag in its results:

.. code-block:: yaml

   url: https://example.org/
   filter:
     - css:
         selector: 'body'
         exclude: 'a'

.. _element-by-:

``element-by-``
---------------

The filters **element-by-class**, **element-by-id**, **element-by-style**,
and **element-by-tag** allow you to select all matching instances of a given
HTML element. 

Examples:

To extract only the ``<body>`` of a page: 

.. code-block:: yaml

   url: https://thp.io/2008/urlwatch/
   filter:
     - element-by-tag: body


To extract ``<div id="something">.../<div>`` from a page:

.. code-block:: yaml

   url: http://example.org/
   filter:
     - element-by-id: something

Since you can chain filters, use this to extract an element within another
element:

.. code-block:: yaml

   url: http://example.org/
   filter:
     - element-by-id: container_1
     - element-by-id: something_inside

To make the output human-friendly you can chain html2text on the result:

.. code-block:: yaml

   url: http://example.net/
   filter: 
     - element-by-id: container_1
     - element-by-id: something_inside
     - html2text: pyhtml2text

.. _html2text:

``html2text``
-------------

This filter converts HTML (or XML) to plaintext

**Optional keys**
"""""""""""""""""

* ``method``: One of:
   * ``pyhtml2text``: Uses the `html2text <https://pypi.org/project/html2text/>`__ Python package
   * ``lynx``: Calls the ``lynx`` program
   * ``html2text``: Calls the ``html2text`` program
   * ``bs4``: Uses the `BeautifulSoup <https://pypi.org/project/beautifulsoup4/>`__ Python package
   * ``re``: a simple regex-based tag stripper
 

``pyhtml2text``
^^^^^^^^^^^^^^^
This filter converts HTML into `Markdown <https://www.markdownguide.org/>`__.
using the `html2text <https://pypi.org/project/html2text/>`__ Python package.

It is the recommended option to convert all types of HTML into readable text.

**Optional sub-keys**
~~~~~~~~~~~~~~~~~~~~~

* See `documentation <https://github.com/Alir3z4/html2text/blob/master/docs/usage.md#available-options>`__

**Example configuration**
~~~~~~~~~~~~~~~~~~~~~~~~~

The configuration below overrides the defauts to ensure that accented
characters are kept as they are (`unicode_snob: true`), lines aren't chopped up
(`body_width: 0`), additional empty lines aren't added between sections 
(`single_line_break: true`), and images are ignored (`ignore_images: true`).
If the content has tables, adding `pad_tables: true` *may* improve readability.

.. code-block:: yaml

    filter:
      - xpath: '//section[@role="main"]'
      - html2text:
          method: pyhtml2text
          unicode_snob: true
          body_width: 0
          single_line_break: true
          ignore_images: true
          pad_tables: true


**Required packages**
"""""""""""""""""""""

To run jobs with this filter, you need to install the
`html2text <https://pypi.org/project/html2text/>`__ Python package:


.. code-block:: bash

   pip install --upgrade html2text



``lynx``
^^^^^^^^

This filter calls the `lynx <https://lynx.invisible-island.net/>`__ program (a
text web browser) with the command 
``lynx -nonumbers -dump -assume_charset UTF-8 -display_charset UTF-8``.

**Optional sub-keys**
~~~~~~~~~~~~~~~~~~~~~

* See the ``lynx -help`` output or the `documenation <https://linux.die.net/man/1/lynx>`__  for options that work with ``-dump``

**Required packages**
"""""""""""""""""""""

To run jobs with this filter, you need to have the
`lynx <https://lynx.invisible-island.net/>`__ executable installed.
Please refer to your OS' package installer for instructions.


``html2text``
^^^^^^^^^^^^^

This filter calls the `html2text <https://github.com/grobian/html2text>`__
(HTML to text rendering aimed for E-mail) program with the command
``html2text -nobs -utf8``.

For historical reasons it's the default ``method`` if none is specified.

**Optional sub-keys**
~~~~~~~~~~~~~~~~~~~~~

* See https://linux.die.net/man/1/html2text


**Required packages**
"""""""""""""""""""""

To run jobs with this filter, you need to have the
`html2text <https://github.com/grobian/html2text>`__ executable installed.
Please refer to your OS' package installer for instructions.


``bs4``
^^^^^^^

This filter extract unfromatted text from HTML using the `BeautifulSoup 
<https://pypi.org/project/beautifulsoup4/>`__, specifically its
`get_text(strip=True) 
<https://www.crummy.com/software/BeautifulSoup/bs4/doc/#get-text>`__ method.

Note that as of Beautiful Soup version 4.9.0, when lxml or html.parser are in 
use, the contents of <script>, <style>, and <template> tags are not considered
to be ‘text’, since those tags are not part of the human-visible content of the
page.

**Optional sub-keys**
~~~~~~~~~~~~~~~~~~~~~

* ``parser`` (defaults to ``lxml``): as per `documentation <https://www.crummy.com/software/BeautifulSoup/bs4/doc/#specifying-the-parser-to-use>`__ 

``re``
^^^^^^

A simple HTML/XML tag stripper based on applying a regex.  Very fast but may
not yield the prettiest results.


.. _beautify:

``beautify``
------------

This filter uses the `BeautifulSoup 
<https://pypi.org/project/beautifulsoup4/>`__, `jsbeautifier
<https://pypi.org/project/jsbeautifier/>`__ and `cssbeautifier
<https://pypi.org/project/cssbeautifier/>`__ Python packages to reformat an
HTML document to make it more readable.

**Required packages**
"""""""""""""""""""""

To run jobs with this filter, you need to install the `BeautifulSoup 
<https://pypi.org/project/beautifulsoup4/>`__, `jsbeautifier
<https://pypi.org/project/jsbeautifier/>`__ and `cssbeautifier
<https://pypi.org/project/cssbeautifier/>`__ Python packages:

.. code-block:: bash

   pip install --upgrade beautifulsoup4 jsbeautifier cssbeautifier


.. _pdf2text:

``pdf2text``
------------

This filter converts a PDF file to plaintext using the `pdftotext 
<https://github.com/jalan/pdftotext/blob/master/README.md#pdftotext>`__ Python
library, itself based on the `Poppler <https://poppler.freedesktop.org/>`__ 
library.

This filter *must* be the first filter in a chain of filters.

**Optional sub-keys**
"""""""""""""""""""""

* ``password``: password for a password-protected PDF file

**Required packages**
"""""""""""""""""""""

To run jobs with this filter, you need to install the
`pdftotext <https://pypi.org/project/pdftotext/>`__
Python library and any of its OS-specific Poppler dependencies (see 
`website <https://github.com/jalan/pdftotext/blob/master/README.md#os-dependencies>`__).

.. code-block:: bash

   pip install --upgrade pdftotext
   # additional OS-specific commands as per documentation


Example:

.. code-block:: yaml

   name: "Convert PDF to text"
   url: https://example.net/sample.pdf
   filter: 
     - pdf2text:
         password: pdfpassword


.. _format-json:

``format-json``
---------------

This filter deserializes a JSON object and reformats it using Python's 
`json.dumps <https://docs.python.org/3/library/json.html#json.dumps>`__
with indentations.

**Optional sub-keys**
"""""""""""""""""""""

* ``indentation`` (defaults to 4): indent to pretty-print JSON array elements. ``None`` selects the most compact representation.


.. _ical2text:

``ical2text``
-------------

This filter reads an iCalendar document and converts them to easy-to read text

.. code-block:: yaml

   name: "Make iCal file readable test"
   url: https://example.com/cal.ics
   filter:
     - ical2text:



**Required packages**
"""""""""""""""""""""

To run jobs with this filter, you need to install the
`vobject <https://pypi.org/project/vobject/>`__
Python library.


.. _hexdump:

``hexdump``
-----------

This filter display the contents both in binary and ASCII (hex dump format).

.. code-block:: yaml

   name: "Display binary and ASCII test"
   command: 'cat testfile'
   filter:
     - hexdump:



.. _sha1sum:

``sha1sum``
-----------

This filter calculates a SHA-1 hash for the document,

.. code-block:: yaml

   name: "Calculate SHA-1 hash test"
   url: https://example.com/
   filter:
     - sha1sum:


.. _grep:

``grep`` 
--------

This filter emulates Linux's `grep` using Pyton's 
`regular expression matching <https://docs.python.org/3/library/re.html>`__
(regex) and keeps only lines that match the pattern, discarding the others.
Note that mothwistanding its name, this filter does **not** use the executable
`grep`.

Example: convert HTML to text, strip whitespace, and only keep lines that have
the sequence ``a,b:`` in them:

.. code-block:: yaml

   name: "Grep line matching test"
   url: https://example.org/
   filter:
     - html2text:
     - strip:
     - grep: 'a,b:'

Example: keep only lines that contain "error" irrespective of its case
(e.g. Error, ERROR, etc.):

.. code-block:: yaml

   name: "Lines with error in them, case insensitive"
   url: https://example.org/
   filter:
     - grep: '(?i)error'


.. _grepi:

``grepi`` 
---------

This filter is the inverse of ``grep``  above and keeps only lines that do
not match the `regular expression
<https://docs.python.org/3/library/re.html#regular-expression-syntax>`__,
discarding the others.

Example: eliminate lines that contain "xyz":

.. code-block:: yaml

   name: "Lines with error in them, case insensitive"
   url: https://example.org/
   filter:
     - grepi: 'xyz'


.. _re.sub:

``re.sub``
----------

This filter removes or replaces text using `regular expressions
<https://docs.python.org/3/library/re.html#regular-expression-syntax>`__.

Just like Python’s `re.sub <https://docs.python.org/3/library/re.html#re.sub>`__
function, there’s the possibility to apply a regular expression and either 
remove of replace the matched text. The following example applies the filter
3 times:

1. Just specifying a string as the value will remove the matches.
2. Simple patterns can be replaced with another string using ``pattern``
   as the expression and ``repl`` as the replacement.
3. You can use regex groups (``()``) and back-reference them with ``\1``
   (etc..) to put groups into the replacement string.

All features are described in Python’s re.sub
`documentation <https://docs.python.org/3/library/re.html#re.sub>`__.
The ``pattern`` and ``repl`` values are passed to this
function as-is.

.. code-block:: yaml

   name: "re.sub test"
   url: https://example.com/
   filter:
     - re.sub: '\s*href="[^"]*"'
     - re.sub:
         pattern: '<h1>'
         repl: 'HEADING 1: '
     - re.sub:
         pattern: '</([^>]*)>'
         repl: '<END OF TAG \1>'


**Optional sub-keys**
"""""""""""""""""""""

* ``pattern``: pattern to be replaced. This sub-key must be specified if also using the ``repl`` sub-key. Otherwise the pattern can be specified as the value of ``re.sub``.
* ``repl``: the string for replacement. If this sub-key is missing, defaults to empty string (i.e. deletes the string matched in ``pattern``)


.. _strip:

``strip``
---------

This filter removes leading and trailing whitespace.  It applies to the entire
document: it is **not** applied line-by line.

.. code-block:: yaml

   name: "Stripping leading and trailing whitespace test"
   url: https://example.com/
   filter:
     - strip:


.. _sort:

``sort``
--------

This filter performs a line-based sorting, ignoring cases (case folding as per
Python's `implementation <https://docs.python.org/3/library/stdtypes.html#str.casefold>`__

If the source provides data in random order, you should sort it before
the comparison in order to avoid diffing based only on changes in the sequence.

.. code-block:: yaml

   name: "Sorting lines test"
   url: https://example.net/
   filter:
     - sort: