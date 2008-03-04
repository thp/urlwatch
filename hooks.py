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
    return data

