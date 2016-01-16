URLWATCH README
===============

ABOUT
-----

This is a simple URL watcher, designed to send you diffs of webpages as they
change. Ideal for watching web pages of university courses, so you always
know when lecture dates have changed or new tasks are online :)


DEPENDENCIES
------------

urlwatch requires Python 3.3 or newer.

The dependencies can be installed with (add "--user" to install to $HOME):

    python3 -m pip install pyyaml minidb keyring


QUICK START
-----------

1. Start "urlwatch"
2. Edit and rename the examples in ~/.urlwatch/
3. Add "urlwatch" to your crontab (crontab -e)
4. Receive change notifications via e-mail
5. Customize your hooks in ~/.urlwatch/lib/


FREQUENTLY ASKED QUESTIONS
--------------------------

Q: How do I add/remove URLs?  
A: Edit ~/.urlwatch/urls.txt

Q: A page changes some content on every reload. How do I prevent urlwatch
   from always displaying these changes?  
A: Edit ~/.urlwatch/lib/hooks.py and implement your filters there. Examples
   are included in the urlwatch source distribution.

Q: How do I configure urlwatch as a cron job?  
A: Use "crontab -e" to add the command "urlwatch" to your crontab. Make sure
   stdout of your cronjobs is mailed to you, so you also get the notifications.

Q: Is there an easy way to show changes of .ics files?  
A: Indeed there is. See the example hooks.py file.

Q: What about badly-formed HTML (long lines, etc..)?  
A: Use python-utidylib. See the example hooks.py file.

Q: Is there a way to make the output more human-readable?  
Q: Is there a way to turn it into a diff of parsed HTML perhaps?  
A: Of course. See the example hooks.py file -> use html2txt.html2text(data)

Q: Why do I get an error with URLs with spaces in them?  
A: Please make sure to URL-encode the URLs properly. Use %20 for spaces.

Q: The website I want to watch requires a POST request. How do I send one?  
A: Add the POST data in the same line, separated by a single space. The format
   in urls.txt is: http://example.org/script.cgi value=5&q=search&button=Go

Q: The SMTP server I use requires TLS and authentication to port 587. How do I do that?  
A: Add your password to keyring using:

    urlwatch -s smtp.example.com:587 -f alice@example.com --pass

   Then run urlwatch with --tls and --auth supplied:

    urlwatch -s smtp.example.com:587 -f alice@example.com -t bob@example.com --tls --auth ...


CONTACT
-------

Website: http://thp.io/2008/urlwatch/  
E-Mail: m@thp.io  
Jabber/XMPP: thp@jabber.org
