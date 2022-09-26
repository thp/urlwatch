.. _configuration:

Configuration
=============

.. only:: man

   Synopsis
   --------

   urlwatch --edit-config

   Description
   -----------


The global configuration for urlwatch contains basic settings for the generic
behavior of urlwatch as well as the :ref:`reporters`.

.. only:: html or pdf

    You can edit it with:

    .. code:: bash

       urlwatch --edit-config

.. _configuration_display:

Display
-------

In addition to always reporting changes (which is the whole point of urlwatch),
urlwatch by default reports newly-added (``new``) pages and errors (``error``).
You can change this behavior in the ``display`` section of the configuration:

.. code:: yaml

   display:
     new: true
     error: true
     unchanged: false
     empty-diff: true

If you set ``unchanged`` to ``true``, urlwatch will always report all pages
that are checked but have not changed.

The ``empty-diff`` settings control what happens if a page is ``changed``, but
due to e.g. a ``diff_filter`` the diff is reduced to the empty string. If set
to ``true``, urlwatch will report an (empty) change. If set to ``false``, the
change will not be included in the report.


Filter changes are not applied for ``unchanged``
************************************************

Due to the way the filtered output is stored, ``unchanged`` will always report
the old contents with the filters at the time of retrieval, meaning that any
changes you do to the ``filter`` of a job will not be visible in the
``unchanged`` report. When the page changes, the new filter will be applied.

For this reason, ``unchanged`` cannot be used to test filters, you should use
the ``--test-filter`` command line option to apply your current filter to the
current page contents.


Reporters
---------


.. only:: html or pdf

    Configuration of reporters is described in :ref:`reporters`.

.. only:: man

    See :manpage:`urlwatch-reporters(5)` on the available reporters.

Here is an example configuration that reports on standard
output in color, as well as HTML e-mail using ``sendmail``:

.. code:: yaml

   report:
     text:
       details: true
       footer: true
       line_length: 75
     html:
       diff: unified
       separate: true
     email:
       enabled: true
       method: sendmail
       sendmail:
           path: /usr/sbin/sendmail
       from: 'urlwatch@example.org'
       to: 'you@example.org'
       html: true
       subject: '{count} changes: {jobs}'
     stdout:
       color: true
       enabled: true

Any reporter-specific configuration must be below the ``report`` key
in the configuration.

Configuration settings like ``text``, ``html`` and ``markdown`` will
apply to all reporters that derive from that reporter (for example,
the ``stdout`` reporter uses ``text``, while the ``email`` reporter
with ``html: true`` set uses ``html``).

Setting ``separate: true`` will cause the reporter to send a report for
each job rather than a combined report for all jobs.

.. _job_defaults:

Job Defaults
------------

If you want to change some settings for all your jobs, edit the
``job_defaults`` section in your config file:

.. code-block:: yaml

   job_defaults:
     all:
       diff_tool: wdiff
     url:
       ignore_connection_errors: true

The above config file sets all jobs to use ``wdiff`` as diff tool, and all
``url`` jobs to ignore connection errors.

The possible sub-keys to ``job_defaults`` are:

* ``all``: Applies to all your jobs, independent of its kind
* ``shell``: Applies only to ``shell`` jobs (with key ``command``)
* ``url``: Applies only to ``url`` jobs (with key ``url``)
* ``browser``: Applies only to ``browser`` jobs (with key ``navigate``)

See :ref:`jobs` about the different job kinds and what the possible keys are.

.. only:: man

    Files
    -----

    ``$XDG_CONFIG_HOME/urlwatch/urlwatch.yaml``

    See also
    --------

    :manpage:`urlwatch(1)`,
    :manpage:`urlwatch-reporters(5)`,
    :manpage:`urlwatch-intro(7)`,
    :manpage:`urlwatch-cookbook(7)`

