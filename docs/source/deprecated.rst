Deprecated Features
===================

This page lists the features that are deprecated and steps to
update your configuration to use the replacements (if any).

string-based filter definitions (since 2.19)
--------------------------------------------

With urlwatch 2.19, string-based filter lists are deprecated,
because they are not as flexible as dict-based filter lists
and had some problems (e.g. ``:`` and ``,`` are treated in a
special way and cannot be used in subfilters easily).
If you have a filter definition like this:

.. code:: yaml

   filter: css:body,html2text:re,strip

You can get the same results with a filter definition like this:

.. code:: yaml

   filter:
     - css:
         selector: body
     - html2text:
         method: re
     - strip

Since ``selector`` is the default subfilter for ``css``, and ``method``
is the default subfilter for ``html2text``, this can also be written as:

.. code:: yaml

   filter:
     - css: body
     - html2text: re
     - strip

If you just have a single filter such as:

.. code:: yaml

   filter: html2text

You can change this filter to dict-based using:

.. code:: yaml

   filter:
     - html2text
