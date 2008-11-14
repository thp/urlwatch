#!/usr/bin/python
# Convert iCalendar data to plaintext (very basic, don't rely on it :)
# Requirements: python-vobject (http://vobject.skyhouseconsulting.com/)
# Thomas Perl <thpinfo.com>; Fri, 14 Nov 2008 12:26:42 +0100
# Website: http://thpinfo.com/2008/urlwatch/

def ical2text(ical_string):
    import vobject
    result = []
    if isinstance(ical_string, unicode):
        parsedCal = vobject.readOne(ical_string)
    else:
        try:
            parsedCal = vobject.readOne(ical_string)
        except:
            parsedCal = vobject.readOne(ical_string.decode('utf-8', 'ignore'))

    for event in parsedCal.getChildren():
        if event.name == 'VEVENT':
            if hasattr(event, 'dtstart'):
                start = event.dtstart.value.strftime('%F %H:%M')
            else:
                start = 'unknown start date'

            if hasattr(event, 'dtend'):
                end = event.dtend.value.strftime('%F %H:%M')
            else:
                end = start

            if start == end:
                date_str = start
            else:
                date_str = '%s -- %s' % (start, end)

            result.append('%s: %s' % (date_str, event.summary.value))

    return '\n'.join(result)

if __name__ == '__main__':
    import sys

    if len(sys.argv) == 2:
        print ical2text(open(sys.argv[1]).read())
    else:
        print 'Usage: %s icalendarfile.ics' % (sys.argv[0])
        sys.exit(1)

