.. _dependencies:

Dependencies
============

Python version
--------------

`urlwartch` requires `Python <https://www.python.org/>`__ 3.5 or higher to run.

Mandatory Packages
------------------

When installed with pip or similar package managers, these mandatory packages will be
installed automatically: `appdirs <https://pypi.org/project/appdirs/>`__,
`cssselect <https://pypi.org/project/cssselect/>`__, 
`keyring <https://pypi.org/project/kayring/>`__,
`lxml <https://pypi.org/project/lxml/>`__,
`minidb <https://pypi.org/project/minidb/>`__,
`PyYAML <https://pypi.org/project/PyYAML/>`__, and
`requests <https://pypi.org/project/requests/>`__.


Optional Packages
-----------------

Certain features require additional packages. These optional packages can be installed using: 
(add ``--user`` to install to ``$HOME``)

.. code-block:: bash

    python3 -m pip install <packagename>

Where ``<packagename>`` is one of the following:

+-------------------------+-------------------------------------------------------------------------------+
| Feature                 | Python package(s) to install                                                  |
+=========================+===============================================================================+
| `browser` job kind      | `requests-html <https://pypi.org/project/requests-html/>`__                   |
+-------------------------+-------------------------------------------------------------------------------+
| `pyhtml2text` method    | `html2text <https://pypi.org/project/html2text/>`__                           |
| of `html2text` filter   |                                                                               |
+-------------------------+-------------------------------------------------------------------------------+
| `beautify` filter       | `beautifulsoup4 <https://pypi.org/project/beautifulsoup4/>`__,                |
|                         | `jsbeautifier <https://pypi.org/project/jsbeautifier/>`__ and                 |
|                         | `cssbeautifier <https://pypi.org/project/cssbeautifier/>`__                   |
+-------------------------+-------------------------------------------------------------------------------+
| `pdf2text` filter       | `pdftotext <https://github.com/jalan/pdftotext/>`__ and                       |
|                         | its OS-specific Poppler dependencies (see `website                            |
|                         | <https://github.com/jalan/pdftotext/blob/master/README.md#os-dependencies>`__)|
+-------------------------+-------------------------------------------------------------------------------+
| `ical2text` filter      | `vobject <https://pypi.org/project/vobject/>`__                               |
+-------------------------+-------------------------------------------------------------------------------+
| Pushover reporter       | `chump <https://pypi.org/project/chump/>`__                                   |
+-------------------------+-------------------------------------------------------------------------------+
| Pushbullet reporter     | `pushbullet.py <https://pypi.org/project/pushbullet.py/>`__                   |
+-------------------------+-------------------------------------------------------------------------------+
| Matrix reporter         | `matrix_client <https://pypi.org/project/matrix-client/>`__                   |
|                         | and `markdown2 <https://pypi.org/project/markdown2/>`__                       |
+-------------------------+-------------------------------------------------------------------------------+
| `stdout` reporter       | `colorama <https://pypi.org/project/colorama/>`__                             |
| with color on Windows   |                                                                               |
+-------------------------+-------------------------------------------------------------------------------+
| Unit testing            | `pycodestyle <https://pypi.org/project/pycodestyle/>`__                       |
+-------------------------+-------------------------------------------------------------------------------+

Optional Executables
--------------------

Certain features require executables to be installed in your system if they are not already
present. Refer to your OS-specific package manager for their installation.

+-------------------------+-------------------------------------------------------------------------------+
| Feature                 | Executable(s) required                                                        |
+=========================+===============================================================================+
| `lynx` filter           | `lynx <https://lynx.invisible-island.net/>`__ executable                      |
+-------------------------+-------------------------------------------------------------------------------+
| `html2text` method      | `html2text <https://github.com/grobian/html2text>`__ executable               |
| of `html2text` filter   |                                                                               |
+-------------------------+-------------------------------------------------------------------------------+
