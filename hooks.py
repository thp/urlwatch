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

        REMOVE_TAGS = ['applet', 'area', 'audio', 'audio', 'background-color', 'background-image',
                       'background-position', 'background-repeat', 'background-size', 'base', 'basefont', 'bdi', 'bdo',
                       'big', 'border-bottom-color', 'border-bottom-left-radius', 'border-bottom-right-radius',
                       'border-bottom-style', 'border-bottom-width', 'border-left-color', 'border-left-style',
                       'border-left-width', 'border-right-color', 'border-right-style', 'border-right-width',
                       'border-top-color', 'border-top-left-radius', 'border-top-right-radius', 'border-top-style',
                       'border-top-width', 'box-shadow', 'br', 'canvas', 'center', 'clear', 'colgroup', 'color',
                       'datalist', 'display', 'embed', 'float', 'font-family', 'font-size', 'font-style', 'font-weight',
                       'form', 'frameset', 'head', 'hr', 'img', 'input', 'line-height', 'link', 'list-style-image',
                       'list-style-position', 'list-style-type', 'map', 'margin-bottom', 'margin-left', 'margin-right',
                       'margin-top', 'meta', 'noframes', 'noscript', 'object', 'opacity', 'optgroup', 'option',
                       'outline-color', 'outline-style', 'outline-width', 'padding-bottom', 'padding-left',
                       'padding-right', 'padding-top', 'param', 'position', 'progress', 'rp', 'rt', 'ruby', 'script',
                       'script', 'select', 'source', 'style', 'style', 'table', 'text-align', 'text-decoration',
                       'text-indent', 'text-shadow', 'textarea', 'title', 'track', 'vertical-align', 'video',
                       'visibility', 'xmp']

        PRESERVE_ATTRIBUTES = ['href', 'title', 'target', 'src', 'alt']
        # PRESERVE_ATTRIBUTES.append(['id', 'class'])

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
                tag.attrs = {key: value for key, value in tag.attrs.items() if key in PRESERVE_ATTRIBUTES}
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

        preserved_attrs = sorted(preserved_attrs.items(), key=lambda x: x[1], reverse=True)
        logger.debug("Removed {0} unwanted attributes from HTML".format(removed_attrs_count))
        logger.debug("Preserved attributes: '{0}'".format(preserved_attrs))

        result = soup.prettify()

        # logger.debug("Cleanup result:\n\n{0}\n\n".format(result))

        return result
