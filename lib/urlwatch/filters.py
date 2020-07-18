# -*- coding: utf-8 -*-
#
# This file is part of urlwatch (https://thp.io/2008/urlwatch/).
# Copyright (c) 2008-2020 Thomas Perl <m@thp.io>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import re
import logging
import itertools
import os
import html.parser
import hashlib
import json
import yaml
import sys
import subprocess

from enum import Enum
from lxml import etree
from lxml.cssselect import CSSSelector

from .util import TrackSubClasses, import_module_from_source

logger = logging.getLogger(__name__)


class FilterBase(object, metaclass=TrackSubClasses):
    __subclasses__ = {}
    __anonymous_subclasses__ = []

    def __init__(self, job, state):
        self.job = job
        self.state = state

    @classmethod
    def filter_documentation(cls):
        result = []
        for sc in TrackSubClasses.sorted_by_kind(cls):
            default_subfilter = getattr(sc, '__default_subfilter__', None)
            result.extend((
                '  * %s - %s' % (sc.__kind__, sc.__doc__),
            ))
            if hasattr(sc, '__supported_subfilters__'):
                for key, doc in sc.__supported_subfilters__.items():
                    result.append('      %s%s%s ... %s' % ('[' if key == default_subfilter else '', key,
                                                           ']' if key == default_subfilter else '', doc))
        result.append('\n[] ... Parameter can be supplied as unnamed value\n')
        return '\n'.join(result)

    @classmethod
    def auto_process(cls, state, data):
        filters = itertools.chain((filtercls for _, filtercls in
                                   sorted(cls.__subclasses__.items(), key=lambda k_v: k_v[0])),
                                  cls.__anonymous_subclasses__)

        for filtercls in filters:
            filter_instance = filtercls(state.job, state)
            if filter_instance.match():
                logger.info('Auto-applying filter %r to %s', filter_instance, state.job.get_location())
                data = filter_instance.filter(data)

        return data

    @classmethod
    def normalize_filter_list(cls, filter_spec):
        for filter_kind, subfilter in cls._internal_normalize_filter_list(filter_spec):
            filtercls = cls.__subclasses__.get(filter_kind, None)

            if filtercls is None:
                raise ValueError('Unknown filter kind: {} (subfilter {})'.format(filter_kind, subfilter))

            if getattr(filtercls, '__no_subfilter__', False) and subfilter:
                raise ValueError('No subfilters supported for {}'.format(filter_kind))

            if isinstance(subfilter, dict) and hasattr(filtercls, '__supported_subfilters__'):
                provided_keys = set(subfilter.keys())
                allowed_keys = set(filtercls.__supported_subfilters__.keys())
                unknown_keys = provided_keys.difference(allowed_keys)
                if unknown_keys and '<any>' not in allowed_keys:
                    raise ValueError('Filter "{}" does not support subfilter(s): {} (supported: {})'.format(filter_kind,
                                                                                                            unknown_keys,
                                                                                                            allowed_keys))

            yield filter_kind, subfilter

    @classmethod
    def _internal_normalize_filter_list(cls, filter_spec):
        if isinstance(filter_spec, str):
            old_filter_spec = filter_spec

            # Legacy string-based filter list specification:
            # "filter1:param1,filter2,filter3,filter4:param4"
            filter_spec = [dict([filter_kind.split(':', 1)]) if ':' in filter_kind else filter_kind
                           for filter_kind in filter_spec.split(',')]

            logger.warn('String-based filter definitions (%s) are deprecated, please convert to dict-style:\n\n%s',
                        old_filter_spec, yaml.dump(filter_spec, default_flow_style=False))

        if isinstance(filter_spec, list):
            for item in filter_spec:
                if isinstance(item, str):
                    filter_kind, subfilter = item, None
                elif isinstance(item, dict):
                    filter_kind, subfilter = next(iter(item.items()))

                filtercls = cls.__subclasses__.get(filter_kind, None)

                if isinstance(subfilter, dict):
                    yield filter_kind, subfilter
                elif subfilter is None:
                    yield filter_kind, {}
                elif hasattr(filtercls, '__default_subfilter__'):
                    yield filter_kind, {getattr(filtercls, '__default_subfilter__'): subfilter}
                else:
                    yield filter_kind, subfilter

    @classmethod
    def process(cls, filter_kind, subfilter, state, data):
        logger.info('Applying filter %r, subfilter %r to %s', filter_kind, subfilter, state.job.get_location())
        filtercls = cls.__subclasses__.get(filter_kind, None)
        return filtercls(state.job, state).filter(data, subfilter)

    @classmethod
    def is_bytes_filter(cls, filter):
        return (filter in [name for name, class_ in FilterBase.__subclasses__.items()
                           if getattr(class_, '__uses_bytes__', False)])

    def match(self):
        return False

    def filter(self, data, subfilter):
        raise NotImplementedError()


class AutoMatchFilter(FilterBase):
    """Automatically matches subclass filters with a given location"""
    MATCH = None

    def match(self):
        if self.MATCH is None:
            return False

        d = self.job.to_dict()
        result = all(d.get(k, None) == v for k, v in self.MATCH.items())
        logger.debug('Matching %r with %r result: %r', self, self.job, result)
        return result


class RegexMatchFilter(FilterBase):
    """Same as AutoMatchFilter but matching is done with regexes"""
    MATCH = None

    def match(self):
        if self.MATCH is None:
            return False

        d = self.job.to_dict()

        # It's a match if we have at least one key/value pair that matches,
        # and no key/value pairs that do not match
        matches = [v.match(d[k]) for k, v in self.MATCH.items() if k in d]
        result = len(matches) > 0 and all(matches)
        logger.debug('Matching %r with %r result: %r', self, self.job, result)
        return result


class LegacyHooksPyFilter(FilterBase):
    FILENAME = os.path.expanduser('~/.urlwatch/lib/hooks.py')

    def __init__(self, job, state):
        super().__init__(job, state)

        self.hooks = None
        if os.path.exists(self.FILENAME):
            try:
                self.hooks = import_module_from_source('legacy_hooks', self.FILENAME)
            except Exception as e:
                logger.error('Could not load legacy hooks file: %s', e)

    def match(self):
        return self.hooks is not None

    def filter(self, data, subfilter):
        try:
            result = self.hooks.filter(self.job.get_location(), data)
            if result is None:
                result = data
            return result
        except Exception as e:
            logger.warn('Could not apply legacy hooks filter: %s', e)
            return data


class BeautifyFilter(FilterBase):
    """Beautify HTML"""

    __kind__ = 'beautify'

    __no_subfilter__ = True

    def filter(self, data, subfilter):
        import jsbeautifier
        import cssbeautifier
        from bs4 import BeautifulSoup as bs
        soup = bs(data, features="lxml")
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string is not None:
                beautified_js = jsbeautifier.beautify(script.string)
                script.string = beautified_js
        styles = soup.find_all('style')
        for style in styles:
            if style.string is not None:
                beautified_css = cssbeautifier.beautify(style.string)
                style.string = beautified_css
        return soup.prettify()


class Html2TextFilter(FilterBase):
    """Convert HTML to plaintext"""

    __kind__ = 'html2text'

    __supported_subfilters__ = {
        'method': 'Method to use for conversion (default: re)',
        '<any>': 'Method-specific options passed to html2text',
    }

    __default_subfilter__ = 'method'

    def filter(self, data, subfilter):
        if 'method' in subfilter:
            method = subfilter['method']
            del subfilter['method']
            options = subfilter
        else:
            method = 're'
            options = {}
        if method == 'pyhtml2text':
            self.job.is_markdown = True
        from .html2txt import html2text
        return html2text(data, baseurl=getattr(self.job, 'url', getattr(self.job, 'navigate', '')),
                         method=method, options=options)


class Pdf2TextFilter(FilterBase):
    """Convert PDF to plaintext"""
    # Requires data to be in bytes (not unicode)
    # Dependency: pdftotext (https://github.com/jalan/pdftotext), itself based
    # on poppler (https://poppler.freedesktop.org/)
    # Note: check pdftotext website for OS-specific dependencies for install

    __kind__ = 'pdf2text'
    __uses_bytes__ = True

    __supported_subfilters__ = {
        'password': 'PDF password for decryption',
    }

    def filter(self, data, subfilter):
        # data must be bytes
        if not isinstance(data, bytes):
            raise ValueError('The pdf2text filter needs bytes input (is it the first filter?)')

        import pdftotext
        import io
        return '\n\n'.join(pdftotext.PDF(io.BytesIO(data), password=subfilter.get('password', '')))


class Ical2TextFilter(FilterBase):
    """Convert iCalendar to plaintext"""

    __kind__ = 'ical2text'

    __no_subfilter__ = True

    def filter(self, data, subfilter):
        from .ical2txt import ical2text
        return ical2text(data)


class JsonFormatFilter(FilterBase):
    """Convert to formatted json"""

    __kind__ = 'format-json'

    __supported_subfilters__ = {
        'indentation': 'Indentation level for pretty-printing',
    }

    __default_subfilter__ = 'indentation'

    def filter(self, data, subfilter):
        indentation = int(subfilter.get('indentation', 4))
        parsed_json = json.loads(data)
        return json.dumps(parsed_json, ensure_ascii=False, sort_keys=True, indent=indentation, separators=(',', ': '))


class GrepFilter(FilterBase):
    """Filter only lines matching a regular expression"""

    __kind__ = 'grep'

    __supported_subfilters__ = {
        're': 'Lines matching this expression are kept (required)',
    }

    __default_subfilter__ = 're'

    def filter(self, data, subfilter):
        if 're' not in subfilter:
            raise ValueError('The grep filter needs a regular expression')

        return '\n'.join(line for line in data.splitlines()
                         if re.search(subfilter['re'], line) is not None)


class InverseGrepFilter(FilterBase):
    """Remove lines matching a regular expression"""

    __kind__ = 'grepi'

    __supported_subfilters__ = {
        're': 'Lines matching this expression are removed (required)',
    }

    __default_subfilter__ = 're'

    def filter(self, data, subfilter):
        if 're' not in subfilter:
            raise ValueError('The inverse grep filter needs a regular expression')

        return '\n'.join(line for line in data.splitlines()
                         if re.search(subfilter['re'], line) is None)


class StripFilter(FilterBase):
    """Strip leading and trailing whitespace"""

    __kind__ = 'strip'

    __no_subfilter__ = True

    def filter(self, data, subfilter):
        return data.strip()


class FilterBy(Enum):
    ATTRIBUTE = 1
    TAG = 2


class ElementsBy(html.parser.HTMLParser):
    def __init__(self, filter_by, name, value=None):
        super().__init__()

        self._filter_by = filter_by
        if self._filter_by == FilterBy.ATTRIBUTE:
            self._attributes = {name: value}
        else:
            self._name = name

        self._result = []
        self._inside = False
        self._elts = []

    def get_html(self):
        return ''.join(self._result)

    def handle_starttag(self, tag, attrs):
        ad = dict(attrs)

        if self._filter_by == FilterBy.ATTRIBUTE and all(ad.get(k, None) == v for k, v in self._attributes.items()):
            self._inside = True
        elif self._filter_by == FilterBy.TAG and tag == self._name:
            self._inside = True

        if self._inside:
            self._result.append('<%s%s%s>' % (tag, ' ' if attrs else '',
                                              ' '.join('%s="%s"' % (k, v) for k, v in attrs)))
            self._elts.append(tag)

    def handle_endtag(self, tag):
        if self._inside:
            self._result.append('</%s>' % (tag,))
            if tag in self._elts:
                t = self._elts.pop()
                while t != tag and self._elts:
                    t = self._elts.pop()
            if not self._elts:
                self._inside = False

    def handle_data(self, data):
        if self._inside:
            self._result.append(data)


class GetElementById(FilterBase):
    """Get an HTML element by its ID"""

    __kind__ = 'element-by-id'

    __supported_subfilters__ = {
        'id': 'ID of the element to filter for (required)',
    }

    __default_subfilter__ = 'id'

    def filter(self, data, subfilter):
        if 'id' not in subfilter:
            raise ValueError('Need an element ID for filtering')

        element_by_id = ElementsBy(FilterBy.ATTRIBUTE, 'id', subfilter['id'])
        element_by_id.feed(data)
        return element_by_id.get_html()


class GetElementByClass(FilterBase):
    """Get all HTML elements by class"""

    __kind__ = 'element-by-class'

    __supported_subfilters__ = {
        'class': 'HTML class attribute to filter for (required)',
    }

    __default_subfilter__ = 'class'

    def filter(self, data, subfilter):
        if 'class' not in subfilter:
            raise ValueError('Need an element class for filtering')

        element_by_class = ElementsBy(FilterBy.ATTRIBUTE, 'class', subfilter['class'])
        element_by_class.feed(data)
        return element_by_class.get_html()


class GetElementByStyle(FilterBase):
    """Get all HTML elements by style"""

    __kind__ = 'element-by-style'

    __supported_subfilters__ = {
        'style': 'HTML style attribute value to filter for (required)',
    }

    __default_subfilter__ = 'style'

    def filter(self, data, subfilter):
        if 'style' not in subfilter:
            raise ValueError('Need an element style for filtering')

        element_by_style = ElementsBy(FilterBy.ATTRIBUTE, 'style', subfilter['style'])
        element_by_style.feed(data)
        return element_by_style.get_html()


class GetElementByTag(FilterBase):
    """Get an HTML element by its tag"""

    __kind__ = 'element-by-tag'

    __supported_subfilters__ = {
        'tag': 'HTML tag name to filter for (required)',
    }

    __default_subfilter__ = 'tag'

    def filter(self, data, subfilter):
        if 'tag' not in subfilter:
            raise ValueError('Need a tag for filtering')

        element_by_tag = ElementsBy(FilterBy.TAG, subfilter['tag'])
        element_by_tag.feed(data)
        return element_by_tag.get_html()


class Sha1Filter(FilterBase):
    """Calculate the SHA-1 checksum of the content"""

    __kind__ = 'sha1sum'

    __no_subfilter__ = True

    def filter(self, data, subfilter):
        sha = hashlib.sha1()
        sha.update(data.encode('utf-8', 'ignore'))
        return sha.hexdigest()


class HexdumpFilter(FilterBase):
    """Convert binary data to hex dump format"""

    __kind__ = 'hexdump'

    __no_subfilter__ = True

    def filter(self, data, subfilter):
        data = bytearray(data.encode('utf-8', 'ignore'))
        blocks = [data[i * 16:(i + 1) * 16] for i in range(int((len(data) + (16 - 1)) / 16))]
        return '\n'.join('%s  %s' % (' '.join('%02x' % c for c in block),
                                     ''.join((chr(c) if (c > 31 and c < 127) else '.')
                                             for c in block)) for block in blocks)


class LxmlParser:
    EXPR_NAMES = {'css': 'a CSS selector',
                  'xpath': 'an XPath expression'}

    def __init__(self, filter_kind, subfilter, expr_key):
        self.filter_kind = filter_kind
        if subfilter is None:
            raise ValueError('Need %s for filtering' % (self.EXPR_NAMES[filter_kind],))
        if isinstance(subfilter, str):
            self.expression = subfilter
            self.method = 'html'
            self.exclude = None
            self.namespaces = None
        elif isinstance(subfilter, dict):
            if expr_key not in subfilter:
                raise ValueError('Need %s for filtering' % (self.EXPR_NAMES[filter_kind],))
            self.expression = subfilter[expr_key]
            self.method = subfilter.get('method', 'html')
            self.exclude = subfilter.get('exclude')
            self.namespaces = subfilter.get('namespaces')
            if self.method not in ('html', 'xml'):
                raise ValueError('%s method must be "html" or "xml", got %r' % (filter_kind, self.method))
            if self.method == 'html' and self.namespaces is not None:
                raise ValueError('Namespace prefixes only supported with "xml" method.')
        else:
            raise ValueError('%s subfilter must be a string or dict' % (filter_kind,))
        self.parser = (etree.HTMLParser if self.method == 'html' else etree.XMLParser)()
        self.data = ''

    def feed(self, data):
        self.data += data

    def _to_string(self, element):
        # Handle "/text()" selector, which returns lxml.etree._ElementUnicodeResult (Issue #282)
        if isinstance(element, str):
            return element

        return etree.tostring(element, pretty_print=True, method=self.method, encoding='unicode', with_tail=False)

    @staticmethod
    def _remove_element(element):
        parent = element.getparent()
        if parent is None:
            # Do not exclude root element
            return
        if isinstance(element, etree._ElementUnicodeResult):
            if element.is_tail:
                parent.tail = None
            elif element.is_text:
                parent.text = None
            elif element.is_attribute:
                del parent.attrib[element.attrname]
        else:
            previous = element.getprevious()
            if element.tail is not None:
                if previous is not None:
                    previous.tail = previous.tail + element.tail if previous.tail else element.tail
                else:
                    parent.text = parent.text + element.tail if parent.text else element.tail
            parent.remove(element)

    def _reevaluate(self, element):
        if self._orphaned(element):
            return None
        if isinstance(element, etree._ElementUnicodeResult):
            parent = element.getparent()
            if parent is None:
                return element
            if element.is_tail:
                return parent.tail
            elif element.is_text:
                return parent.text
            elif element.is_attribute:
                return parent.attrib.get(element.attrname)
        else:
            return element

    def _orphaned(self, element):
        if isinstance(element, etree._ElementUnicodeResult):
            parent = element.getparent()
            if ((element.is_tail and parent.tail is None)
                    or (element.is_text and parent.text is None)
                    or (element.is_attribute and parent.attrib.get(element.attrname) is None)):
                return True
            else:
                element = parent
        try:
            tree = element.getroottree()
            path = tree.getpath(element)
            return element is not tree.xpath(path, namespaces=self.namespaces)[0]
        except (ValueError, IndexError):
            return True

    def _get_filtered_elements(self):
        try:
            root = etree.fromstring(self.data, self.parser)
        except ValueError:
            # Strip XML declaration, for example: '<?xml version="1.0" encoding="utf-8"?>'
            # for https://heronebag.com/blog/index.xml, an error happens, as we get a
            # a (Unicode) string, but the XML contains its own "encoding" declaration
            self.data = re.sub(r'^<[?]xml[^>]*[?]>', '', self.data)
            # Retry parsing with XML declaration removed (Fixes #281)
            root = etree.fromstring(self.data, self.parser)
        if root is None:
            return []
        excluded_elems = None
        if self.filter_kind == 'css':
            selected_elems = CSSSelector(self.expression,
                                         namespaces=self.namespaces).evaluate(root)
            excluded_elems = CSSSelector(self.exclude,
                                         namespaces=self.namespaces).evaluate(root) if self.exclude else None
        elif self.filter_kind == 'xpath':
            selected_elems = root.xpath(self.expression, namespaces=self.namespaces)
            excluded_elems = root.xpath(self.exclude, namespaces=self.namespaces) if self.exclude else None
        if excluded_elems is not None:
            for el in excluded_elems:
                self._remove_element(el)
        return [el for el in map(self._reevaluate, selected_elems) if el is not None]

    def get_filtered_data(self):
        return '\n'.join(self._to_string(element) for element in self._get_filtered_elements())


class CssFilter(FilterBase):
    """Filter XML/HTML using CSS selectors"""

    __kind__ = 'css'

    __supported_subfilters__ = {
        'selector': 'The CSS selector to use for filtering (required)',
        'method': 'The method (html or xml) used for parsing',
        'exclude': 'Elements to remove from the final result',
        'namespaces': 'Mapping of XML namespaces for matching',
    }

    __default_subfilter__ = 'selector'

    def filter(self, data, subfilter):
        lxml_parser = LxmlParser('css', subfilter, 'selector')
        lxml_parser.feed(data)
        return lxml_parser.get_filtered_data()


class XPathFilter(FilterBase):
    """Filter XML/HTML using XPath expressions"""

    __kind__ = 'xpath'

    __supported_subfilters__ = {
        'path': 'The XPath to use for filtering (required)',
        'method': 'The method (html or xml) used for parsing',
        'exclude': 'Elements to remove from the final result',
        'namespaces': 'Mapping of XML namespaces for matching',
    }

    __default_subfilter__ = 'path'

    def filter(self, data, subfilter):
        lxml_parser = LxmlParser('xpath', subfilter, 'path')
        lxml_parser.feed(data)
        return lxml_parser.get_filtered_data()


class RegexSub(FilterBase):
    """Replace text with regular expressions using Python's re.sub"""

    __kind__ = 're.sub'

    __supported_subfilters__ = {
        'pattern': 'Regular expression to search for (required)',
        'repl': 'Replacement string (default: empty string)',
    }

    __default_subfilter__ = 'pattern'

    def filter(self, data, subfilter):
        if 'pattern' not in subfilter:
            raise ValueError('{} needs a pattern'.format(self.__kind__))

        # Default: Replace with empty string if no "repl" value is set
        return re.sub(subfilter['pattern'], subfilter.get('repl', ''), data)


class SortFilter(FilterBase):
    """Sort input items"""

    __kind__ = 'sort'

    __supported_subfilters__ = {
        'reverse': 'Set to true to reverse sorting order',
        'separator': 'Item separator (default: newline)',
    }

    __default_subfilter__ = 'separator'

    def filter(self, data, subfilter):
        reverse = (isinstance(subfilter, dict) and subfilter.get('reverse', False) is True)
        separator = subfilter.get('separator', '\n')
        return separator.join(sorted(data.split(separator), key=str.casefold, reverse=reverse))


class ReverseFilter(FilterBase):
    """Reverse input items"""

    __kind__ = 'reverse'

    __supported_subfilters__ = {
        'separator': 'Item separator (default: newline)',
    }

    __default_subfilter__ = 'separator'

    def filter(self, data, subfilter):
        separator = subfilter.get('separator', '\n')
        return separator.join(reversed(data.split(separator)))


class ShellPipeFilter(FilterBase):
    """Filter using a shell command"""

    __kind__ = 'shellpipe'

    __supported_subfilters__ = {
        'command': 'Shell command to execute for filtering (required)',
    }

    __default_subfilter__ = 'command'

    def filter(self, data, subfilter=None):
        if 'command' not in subfilter:
            raise ValueError('{} filter needs a command'.format(self.__kind__))

        encoding = sys.getdefaultencoding()

        env = {
            'URLWATCH_JOB_NAME': self.job.pretty_name() if self.job else '',
            'URLWATCH_JOB_LOCATION': self.job.get_location() if self.job else '',
        }

        return subprocess.check_output(subfilter['command'], shell=True,
                                       input=data.encode(encoding), env=env).decode(encoding)
