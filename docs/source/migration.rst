Migration from 1.x
==================

Migration from urlwatch 1.x should be automatic on first start. Here is
a quick rundown of changes in 2.0:

-  URLs are stored in a YAML file now, with direct support for
   specifying names for jobs, different job kinds, directly applying
   filters, selecting the HTTP request method, specifying POST data as
   dictionary and much more
-  The cache directory has been replaced with a SQLite 3 database file
   “cache.db” in minidb format, storing all change history (use
   ``--gc-cache`` to remove old changes if you don’t need them anymore)
   for further analysis
-  The hooks mechanism has been replaced with support for creating new
   job kinds by subclassing, new filters (also by subclassing) as well
   as new reporters (pieces of code that put the results somewhere, for
   example the default installation contains the “stdout” reporter that
   writes to the console and the “email” reporter that can send HTML and
   text e-mails)
-  A configuration file - urlwatch.yaml - has been added for specifying
   user preferences instead of having to supply everything via the
   command line

