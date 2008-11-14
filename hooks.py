# Example hooks file to go with watch.py
# You can see which filter you want to apply using the URL
# parameter and you can use the "re" module to search for
# the part that you want to filter, so the noise is removed.

import re

def filter(url, data):
    if url == 'http://www.inso.tuwien.ac.at/lectures/usability/':
        return re.sub('.*TYPO3SEARCH_end.*', '', data)
    elif url == 'https://www.auto.tuwien.ac.at/courses/viewDetails/11/':
        return re.sub('</html><!-- \d+ -->', '', data)
    elif url == 'http://grenzlandvagab.gr.funpic.de/events/':
        return re.sub('<!-- Ad by .*by funpic.de -->', '', data)
    elif url == 'http://www.mv-eberau.at/terminliste.php':
        return data.replace('</br>', '\n')
    elif 'iuner.lukas-krispel.at' in url:
        # Remove always-changing entries from FTP server listing
        return re.sub('drwx.*usage', '', re.sub('drwx.*logs', '', data))
    elif url.startswith('http://ti.tuwien.ac.at/rts/teaching/courses/'):
        # example of using the "tidy" module for cleaning up bad HTML
        import tidy
        mlr = re.compile('magicCalendarHeader.*magicCalendarBottom', re.S)
        data = str(tidy.parseString(data, output_xhtml=1, indent=0, tidy_mark=0))
        return re.sub(mlr, '', data)
    elif url == 'http://www.poleros.at/calender.htm':
        # remove style changes, because we only want to see content changes
        return re.sub('style="[^"]"', '', data)
    elif url == 'http://www.ads.tuwien.ac.at/teaching/LVA/186170.html':
        return re.sub('Saved in parser cache with key .* and timestamp .* --', '', re.sub('Served by aragon in .* secs\.', '', re.sub('This page has been accessed .* times\.', '', data)))
    elif url.endswith('.ics') or url == 'http://www.kukuk.at/ical/events':
        # example of generating a summary for icalendar files
        # the ical2txt.py module is included with urlwatch
        import ical2txt
        # append "data" to the converted ical data, so you get
        # all minor changes to the ICS that are not included
        # in the ical2text summary (remove this if you want)
        return ical2txt.ical2text(data).encode('utf-8') + '\n\n' + data
    return data

