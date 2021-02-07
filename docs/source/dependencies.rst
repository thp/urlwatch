.. _dependencies:

Dependencies
============

Mandatory requirements are required to run urlwatch. Depending on what
optional features you want to use, you might also need to install
additional packages -- however, those are not needed to run urlwatch.

Mandatory Packages
------------------

-  Python 3.6 or newer
-  `PyYAML <http://pyyaml.org/>`__
-  `minidb <https://thp.io/2010/minidb/>`__
-  `requests <http://python-requests.org/>`__
-  `keyring <https://github.com/jaraco/keyring/>`__
-  `appdirs <https://github.com/ActiveState/appdirs>`__
-  `lxml <https://lxml.de>`__
-  `cssselect <https://cssselect.readthedocs.io>`__

The dependencies can be installed with (add ``--user`` to install to ``$HOME``):

::

    python3 -m pip install pyyaml minidb requests keyring appdirs lxml cssselect


Optional Packages
-----------------

Optional packages can be installed using::

        python3 -m pip install <packagename>

Where ``<packagename>`` is one of the following:

+-------------------------+---------------------------------------------------------------------+
| Feature                 | Python package(s) to install                                        |
+=========================+=====================================================================+
| Pushover reporter       | `chump <https://github.com/karanlyons/chump/>`__                    |
+-------------------------+---------------------------------------------------------------------+
| Pushbullet reporter     | `pushbullet.py <https://github.com/randomchars/pushbullet.py>`__    |
+-------------------------+---------------------------------------------------------------------+
| Matrix reporter         | `matrix-nio <https://github.com/poljar/matrix-nio>`__               |
|                         | and `markdown2 <https://github.com/trentm/python-markdown2>`__      |
+-------------------------+---------------------------------------------------------------------+
| `stdout` reporter with  | `colorama <https://github.com/tartley/colorama>`__                  |
| color on Windows        |                                                                     |
+-------------------------+---------------------------------------------------------------------+
| `browser` job kind      | `pyppeteer <https://github.com/pyppeteer/pyppeteer>`__              |
+-------------------------+---------------------------------------------------------------------+
| Unit testing            | `pycodestyle <http://pycodestyle.pycqa.org/en/latest/>`__,          |
|                         | `docutils <https://docutils.sourceforge.io>`__,                     |
+-------------------------+---------------------------------------------------------------------+
| Documentation build     | `Sphinx <https://www.sphinx-doc.org/>`__                            |
+-------------------------+---------------------------------------------------------------------+
| `beautify` filter       | `beautifulsoup4 <https://pypi.org/project/beautifulsoup4/>`__;      |
|                         | optional dependencies (for ``<script>`` and ``<style>`` tags):      |
|                         | `jsbeautifier <https://pypi.org/project/jsbeautifier/>`__ and       |
|                         | `cssbeautifier <https://pypi.org/project/cssbeautifier/>`__         |
+-------------------------+---------------------------------------------------------------------+
| `pdf2text` filter       | `pdftotext <https://github.com/jalan/pdftotext>`__ and              |
|                         | its OS-specific dependencies (see the above link)                   |
+-------------------------+---------------------------------------------------------------------+
| `ocr` filter            | `pytesseract <https://github.com/madmaze/pytesseract>`__ and        |
|                         | `Pillow <https://python-pillow.org>`__ and Tesseract OCR)           |
+-------------------------+---------------------------------------------------------------------+
| XMPP reporter           |`aioxmpp <https://github.com/horazont/aioxmpp>`__                    |
+-------------------------+---------------------------------------------------------------------+
| `jq` filter             | `jq <https://github.com/mwilliamson/jq.py>`__                       |
+-------------------------+---------------------------------------------------------------------+
