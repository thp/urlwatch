:orphan:

Manpage
=======

Synopsis
--------

urlwatch [options] [JOB ...]

Description
-----------

urlwatch is intended to help you watch changes in webpages and get
notified (via e-mail, in your terminal or through various third party
services) of any changes. The change notification will include the URL
that has changed and a unified diff of what has changed.

See :manpage:`urlwatch-intro(7)` for a quick start guide and tutorial,
and :manpage:`urlwatch-cookbook(7)` for usage recipes and tricks.

This manpage describes the CLI tool.

positional arguments:
   JOB
          indexes or tags of job(s) to run.
          If --tags is set, each JOB is a tag,
          if not, each JOB is an index numbered according to the --list command.

optional arguments:
   -h, --help
          show this help message and exit

   --tags
          use tags instead of indexes to select jobs to run

   --version
          show program's version number and exit

   -v, --verbose
          show debug output

files and directories:
   --urls FILE
          read job list (URLs) from FILE

   --config FILE
          read configuration from FILE

   --hooks FILE
          use FILE as hooks.py module

   --cache FILE
          use FILE as cache database

Authentication:
   --smtp-login
          Enter password for SMTP (store in keyring)

   --xmpp-login
          Enter password for XMPP (store in keyring)

   --telegram-chats
          List telegram chats the bot is joined to

   --test-reporter REPORTER
          Send a test notification

job list management:
   --list
          list jobs

   --add JOB
          add job (key1=value1,key2=value2,...)

   --delete JOB
          delete job by location or index

   --enable JOB
          enable job by location or index

   --disable JOB
          delete job by location or index

   --change_location JOB NEW_LOCATION
          change the location of an existing job by location or index

   --test-filter JOB
          test filter output of job by location or index

   --test-diff-filter JOB
          test diff filter output of job by location or index (needs at least 2 snapshots)

   --dump-history JOB
          dump historical cached data for a job

interactive commands ($EDITOR/$VISUAL):
   --edit
          edit URL/job list

   --edit-config
          edit configuration file

   --edit-hooks
          edit hooks script

miscellaneous:
   --features
          list supported jobs/filters/reporters

   --gc-cache RETAIN_LIMIT
          remove old cache entries, keeping the latest RETAIN_LIMIT (default: 1)


Files
-----

``$XDG_CONFIG_HOME/urlwatch/urls.yaml``
      Configured job and filter list, see :manpage:`urlwatch-jobs(5)` and :manpage:`urlwatch-filters(5)`

``$XDG_CONFIG_HOME/urlwatch/urlwatch.yaml``
      Global and reporter settings, see :manpage:`urlwatch-config(5)` and :manpage:`urlwatch-reporters(5)`

``$XDG_CONFIG_HOME/urlwatch/hooks.py``
      A Python 3 module that can implement new job types, filters and reporters

``$XDG_CACHE_HOME/urlwatch/cache.db``
      A SQLite 3 database (minidb) that contains the state history of jobs (for diffing)


See also
--------

:manpage:`urlwatch-intro(7)`,
:manpage:`urlwatch-cookbook(7)`,
:manpage:`urlwatch-deprecated(7)`,
:manpage:`urlwatch-jobs(5)`,
:manpage:`urlwatch-filters(5)`,
:manpage:`urlwatch-config(5)`,
:manpage:`urlwatch-reporters(5)`


Author
------

Thomas Perl <https://thp.io/>


Bug Tracker
-----------

https://github.com/thp/urlwatch/issues


Website
-------

https://thp.io/2008/urlwatch/
