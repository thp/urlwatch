# -*- coding: utf-8 -*-
#
# This file is part of urlwatch (https://thp.io/2008/urlwatch/).
# Copyright (c) 2008-2023 Thomas Perl <m@thp.io>
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


import logging

import pyppeteer
import asyncio
import threading

from .cli import setup_logger

logger = logging.getLogger(__name__)


class BrowserLoop(object):
    def __init__(self):
        self._event_loop = asyncio.new_event_loop()
        self._browser = self._event_loop.run_until_complete(self._launch_browser())
        self._loop_thread = threading.Thread(target=self._event_loop.run_forever)
        self._loop_thread.start()

    @asyncio.coroutine
    def _launch_browser(self):
        browser = yield from pyppeteer.launch()
        for p in (yield from browser.pages()):
            yield from p.close()
        return browser

    @asyncio.coroutine
    def _get_content(self, url, wait_until=None, useragent=None):
        context = yield from self._browser.createIncognitoBrowserContext()
        page = yield from context.newPage()
        opts = {}
        if wait_until is not None:
            opts['waitUntil'] = wait_until
        if useragent is not None:
            yield from page.setUserAgent(useragent)
        yield from page.goto(url, opts)
        content = yield from page.content()
        yield from context.close()
        return content

    def process(self, url, wait_until=None, useragent=None):
        coroutine = self._get_content(url, wait_until=wait_until, useragent=useragent)
        return asyncio.run_coroutine_threadsafe(coroutine, self._event_loop).result()

    def destroy(self):
        self._event_loop.call_soon_threadsafe(self._event_loop.stop)
        self._loop_thread.join()
        self._loop_thread = None
        self._event_loop.run_until_complete(self._browser.close())
        self._browser = None
        self._event_loop = None


class BrowserContext(object):
    _BROWSER_LOOP = None
    _BROWSER_LOCK = threading.Lock()
    _BROWSER_REFCNT = 0

    def __init__(self):
        with BrowserContext._BROWSER_LOCK:
            if BrowserContext._BROWSER_REFCNT == 0:
                logger.info('Creating browser main loop')
                BrowserContext._BROWSER_LOOP = BrowserLoop()
            BrowserContext._BROWSER_REFCNT += 1

    def process(self, url, wait_until=None, useragent=None):
        return BrowserContext._BROWSER_LOOP.process(url, wait_until=wait_until, useragent=useragent)

    def close(self):
        with BrowserContext._BROWSER_LOCK:
            BrowserContext._BROWSER_REFCNT -= 1
            if BrowserContext._BROWSER_REFCNT == 0:
                logger.info('Destroying browser main loop')
                BrowserContext._BROWSER_LOOP.destroy()
                BrowserContext._BROWSER_LOOP = None


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Browser handler')
    parser.add_argument('url', help='URL to retrieve')
    parser.add_argument('-v', '--verbose', action='store_true', help='show debug output')
    parser.add_argument('-w',
                        '--wait-until',
                        dest='wait_until',
                        choices=['load', 'domcontentloaded', 'networkidle0', 'networkidle2'],
                        help='When to consider a pageload finished')
    parser.add_argument('-u',
                        '--useragent',
                        dest='useragent',
                        help='Change the useragent (sent by pyppeteer)')
    args = parser.parse_args()

    setup_logger(args.verbose)

    try:
        ctx = BrowserContext()
        print(ctx.process(args.url, wait_until=args.wait_until, useragent=args.useragent))
    finally:
        ctx.close()


if __name__ == '__main__':
    main()
