Deprecated Features
===================

This page lists the features that are deprecated and steps to
update your configuration to use the replacements (if any).


matrix_client optional dependency (since 2.24)
----------------------------------------------
In older versions ``matrix_client`` was used as matrix provider.
This optional dependency is now replaced with ``matrix-nio`` which is both
more featureful (supports encrypted rooms) and more actively maintained.

Configuration is backwards compatible so after updating to 2.23 you
only need to install ``matrix-nio`` and everything should work as previously.

To use encryption you need to update configuration in following ways:

#. Remove ``access_token`` field
#. Add ``user`` field

Here is a sample configuration after update:

.. code:: yaml

    matrix:
      homeserver: https://matrix.org
      room_id: "!roomroomroom:matrix.org"
      user: @botusername:matrix.org
      enabled: true

For more details, check :ref:`Matrix reporter documentation<matrix_reporter>`

Filters without subfilters (since 2.22)
---------------------------------------

In older urlwatch versions, it was possible to write custom
filters that do not take a ``subfilter`` as argument.

If you have written your own filter code like this:

.. code:: python

   class CustomFilter(filters.FilterBase):
       """My old custom filter"""

       __kind__ = 'foo'

       def filter(self, data):
           ...

You have to update your filter to take an optional subfilter
argument (if the filter configuration does not have a subfilter
defined, the value of ``subfilter`` will be ``None``):

.. code:: python

   class CustomFilter(filters.FilterBase):
       """My new custom filter"""

       __kind__ = 'foo'

       def filter(self, data, subfilter):
           ...


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


keyring setting in SMTP reporter configuration (since 2.18)
-----------------------------------------------------------

Since version 2.18, the SMTP reporter configuration now uses ``auth``
to decide if SMTP authentication should be done or not. Previously,
this setting was called ``keyring``. If you have an old configuration
like this:

.. code:: yaml

   report:
     email:
       smtp:
         host: localhost
         keyring: false
         port: 25
         starttls: true
       subject: '{count} changes: {jobs}'

You can change the setting to this (replace ``keyring`` with ``auth``):

.. code:: yaml

   report:
     email:
       smtp:
         host: localhost
         auth: false
         port: 25
         starttls: true
       subject: '{count} changes: {jobs}'
