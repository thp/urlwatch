#
# Example hooks file for urlwatch
#
# Copyright (c) 2008-2016 Thomas Perl <thp.io/about>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
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
#

import json
import logging
import os.path
import re

import requests
from bs4 import BeautifulSoup, Comment
from urlwatch import filters
from urlwatch import jobs
from urlwatch import reporters

logger = logging.getLogger(__name__)


class ContentOnlyFilter(filters.FilterBase):
    """Convert iCalendar to plaintext"""

    __kind__ = 'content_only'

    def filter(self, data, subfilter=None):

        REMOVE_TAGS = ['script', 'style', 'applet', 'area', 'audio', 'base', 'basefont', 'bdi', 'bdo', 'big', 'br',
                          'center', 'colgroup', 'datalist', 'form', 'frameset', 'head', 'link', 'map', 'meta',
                          'noframes', 'noscript', 'optgroup', 'option', 'param', 'rp', 'rt', 'ruby', 'script', 'source',
                          'style', 'title', 'track', 'xmp', 'img', 'canvas', 'input', 'textarea', 'audio', 'video',
                          'hr', 'embed', 'object', 'progress', 'select', 'table', 'margin-left', 'margin-top',
                          'margin-right', 'margin-bottom', 'border-left-color', 'border-left-style',
                          'border-left-width', 'border-top-color', 'border-top-style', 'border-top-width',
                          'border-right-color', 'border-right-style', 'border-right-width', 'border-bottom-color',
                          'border-bottom-style', 'border-bottom-width', 'border-top-left-radius',
                          'border-top-right-radius', 'border-bottom-left-radius', 'border-bottom-right-radius',
                          'padding-left', 'padding-top', 'padding-right', 'padding-bottom', 'background-color',
                          'background-image', 'background-repeat', 'background-size', 'background-position',
                          'list-style-image', 'list-style-position', 'list-style-type', 'outline-color',
                          'outline-style', 'outline-width', 'font-size', 'font-family', 'font-weight', 'font-style',
                          'line-height', 'box-shadow', 'clear', 'color', 'display', 'float', 'opacity', 'text-align',
                          'text-decoration', 'text-indent', 'text-shadow', 'vertical-align', 'visibility', 'position']

        REMOVE_ATTRIBUTES = ['lang', 'language', 'onmouseover', 'onmouseout', 'script', 'style', 'font', 'dir', 'face',
                             'size', 'color', 'style', 'class', 'width', 'height', 'hspace', 'border', 'valign',
                             'align', 'background', 'bgcolor', 'text', 'link', 'vlink', 'alink', 'cellpadding',
                             'cellspacing', 'data-sharebuttons', 'data-href', 'id', 'fck_savedurl', 'role',
                             'frameborder', 'scrolling', 'marginheight', 'data-template', 'datetime', 'marginwidth']


        soup = BeautifulSoup(data, 'lxml')


        # Remove comments
        removed_comment_count = 0
        for comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
            removed_comment = comment.extract()
            removed_comment_count += 1

        logger.debug("Removed {0} comments from HTML".format(removed_comment_count))

        # Remove tags
        removed_tag_count = 0
        for elem in soup.findAll(REMOVE_TAGS):
            removed_tag = elem.extract()
            removed_tag_count += 1

        logger.debug("Removed {0} unwanted tags from HTML".format(removed_tag_count))

        # Remove attributes
        removed_attrs_count = 0
        preserved_attrs = {}
        for tag in soup.findAll(True):

            try:
                attrs_count = len(tag.attrs)
                tag.attrs = {key: value for key, value in tag.attrs.items() if key not in REMOVE_ATTRIBUTES}
                removed_attrs_count += attrs_count - len(tag.attrs)

                for key in tag.attrs.keys():
                    if key in preserved_attrs:
                        preserved_attrs[key] += 1
                    else:
                        preserved_attrs[key] = 1

            except AttributeError:
                # 'NavigableString' object has no attribute 'attrs'
                pass
            except ValueError as e:
                print(e)
                pass

        preserved_attrs = sorted(preserved_attrs.items(), key=lambda x:x[1], reverse=True)
        logger.debug("Removed {0} unwanted attributes from HTML".format(removed_attrs_count))
        logger.debug("Preserved attributes: '{0}'".format(preserved_attrs))

        result = soup.prettify()
        return result

# class CaseFilter(filters.FilterBase):

# """Custom filter for changing case, needs to be selected manually"""
#
#    __kind__ = 'case'
#
#    def filter(self, data, subfilter=None):
#        # The subfilter is specified using a colon, for example the "case"
#        # filter here can be specified as "case:upper" and "case:lower"
#
#        if subfilter is None:
#            subfilter = 'upper'
#
#        if subfilter == 'upper':
#            return data.upper()
#        elif subfilter == 'lower':
#            return data.lower()
#        else:
#            raise ValueError('Unknown case subfilter: %r' % (subfilter,))


# class IndentFilter(filters.FilterBase):
#    """Custom filter for indenting, needs to be selected manually"""
#
#    __kind__ = 'indent'
#
#    def filter(self, data, subfilter=None):
#        # The subfilter here is a number of characters to indent
#
#        if subfilter is None:
#            indent = 8
#        else:
#            indent = int(subfilter)
#
#        return '\n'.join((' '*indent) + line for line in data.splitlines())

# class CustomMatchUrlFilter(filters.AutoMatchFilter):
#     # The AutoMatchFilter will apply automatically to all filters
#     # that have the given properties set
#     MATCH = {'url': 'http://example.org/'}
#
#     def filter(self, data):
#         return data.replace('foo', 'bar')
#
#
# class CustomRegexMatchUrlFilter(filters.RegexMatchFilter):
#     # Similar to AutoMatchFilter
#     MATCH = {'url': re.compile('http://example.org/.*')}
#
#     def filter(self, data):
#         return data.replace('foo', 'bar')
#
#
#
#
# class CustomHtmlFileReporter(reporters.HtmlReporter):
#     """Custom reporter that writes the HTML report to a file"""
#
#     __kind__ = 'custom_html'
#
#     def submit(self):
#         with open(self.config['filename'], 'w') as fp:
#             fp.write('\n'.join(super().submit()))
