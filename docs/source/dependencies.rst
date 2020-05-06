.. _dependencies:

Dependencies
============

Mandatory requirements are required to run urlwatch. Depending on what
optional features you want to use, you might also need to install
additional packages -- however, those are not needed to run urlwatch.

Mandatory Packages
------------------

-  Python 3.5 or newer
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
| Matrix reporter         | `matrix_client <https://github.com/matrix-org/matrix-python-sdk>`__ |
|                         | and `markdown2 <https://github.com/trentm/python-markdown2>`__      |
+-------------------------+---------------------------------------------------------------------+
| `stdout` reporter with  | `colorama <https://github.com/tartley/colorama>`__                  |
| color on Windows        |                                                                     |
+-------------------------+---------------------------------------------------------------------+
| `browser` job kind      | `requests-html <https://html.python-requests.org>`__                |
+-------------------------+---------------------------------------------------------------------+
| Unit testing            | `pycodestyle <http://pycodestyle.pycqa.org/en/latest/>`__           |
+-------------------------+---------------------------------------------------------------------+
| `beautify` filter       | `beautifulsoup4 <https://pypi.org/project/beautifulsoup4/>`__,      |
|                         | `jsbeautifier <https://pypi.org/project/jsbeautifier/>`__ and       |
|                         | `cssbeautifier <https://pypi.org/project/cssbeautifier/>`__         |
+-------------------------+---------------------------------------------------------------------+

