.. highlight:: none

::

                            _               _       _       ____
                 _   _ _ __| |_      ____ _| |_ ___| |__   |___ \
                | | | | '__| \ \ /\ / / _` | __/ __| '_ \    __) |
                | |_| | |  | |\ V  V / (_| | || (__| | | |  / __/
                 \__,_|_|  |_| \_/\_/ \__,_|\__\___|_| |_| |_____|

                                     ... monitors webpages for you


|Build Status| |Packaging status| |PyPI version|

.. |Build Status| image:: https://travis-ci.org/thp/urlwatch.svg
   :target: https://travis-ci.org/thp/urlwatch
.. |Packaging status| image:: https://repology.org/badge/tiny-repos/urlwatch.svg
   :target: https://repology.org/metapackage/urlwatch/versions
.. |PyPI version| image:: https://badge.fury.io/py/urlwatch.svg
   :target: https://badge.fury.io/py/urlwatch

urlwatch is intended to help you watch changes in webpages and get
notified (via e-mail, in your terminal or through various third party
services) of any changes. The change notification will include the URL
that has changed and a unified diff of what has changed.

Quick Start
===========

1. Run ``urlwatch`` once to migrate your old data or start fresh
2. Use ``urlwatch --edit`` to customize your job list (this will
   create/edit ``urls.yaml``)
3. Use ``urlwatch --edit-config`` if you want to set up e-mail sending
4. Add ``urlwatch`` to your crontab (``crontab -e``) to monitor webpages
   periodically

The checking interval is defined by how often you run ``urlwatch``. You
can use e.g. `crontab.guru <https://crontab.guru>`__ to figure out the
schedule expression for the checking interval, we recommend not more
often than 30 minutes (this would be ``*/30 * * * *``). If you have
never used cron before, check out the `crontab command
help <https://www.computerhope.com/unix/ucrontab.htm>`__.

On Windows, ``cron`` is not installed by default. Use the `Windows Task
Scheduler <https://en.wikipedia.org/wiki/Windows_Task_Scheduler>`__
instead, or see `this StackOverflow
question <https://stackoverflow.com/q/132971/1047040>`__ for
alternatives.



The Handbook
============

.. toctree::
   :maxdepth: 2

   introduction
   dependencies
   jobs
   filters
   reporters
   advanced
   deprecated
   migration


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
