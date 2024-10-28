#
# This file is part of urlwatch (https://thp.io/2008/urlwatch/).
# Copyright (c) 2008-2024 Thomas Perl <m@thp.io>
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


import asyncio
import difflib
import re
import email.utils
import itertools
import logging
import sys
import time
import html
import functools
import subprocess

import requests

import urlwatch
from .mailer import SMTPMailer
from .mailer import SendmailMailer
from .util import TrackSubClasses, chunkstring
from .xmpp import XMPP

try:
    import chump
except ImportError:
    chump = None

try:
    from pushbullet import Pushbullet
except ImportError:
    Pushbullet = None

try:
    import matrix_client.api
except ImportError:
    matrix_client = None

try:
    # markdown2 is an optional dependency which provides better formatting for Matrix.
    from markdown2 import Markdown
except ImportError:
    Markdown = None

try:
    from colorama import AnsiToWin32
except ImportError:
    AnsiToWin32 = None

logger = logging.getLogger(__name__)

# Regular expressions that match the added/removed markers of GNU wdiff output
WDIFF_ADDED_RE = r'[{][+].*?[+][}]'
WDIFF_REMOVED_RE = r'[\[][-].*?[-][]]'


class ReporterBase(object, metaclass=TrackSubClasses):
    __subclasses__ = {}

    def __init__(self, report, config, job_states, duration):
        self.report = report
        self.config = config
        self.job_states = job_states
        self.duration = duration

    def get_signature(self):
        return (
            '{pkgname} {version}, {copyright}'.format(pkgname=urlwatch.pkgname,
                                                      version=urlwatch.__version__,
                                                      copyright=urlwatch.__copyright__),
            'Website: {url}'.format(url=urlwatch.__url__),
            'Support urlwatch development: https://github.com/sponsors/thp',
            'watched {count} URLs in {duration} seconds'.format(count=len(self.job_states),
                                                                duration=self.duration.seconds),
        )

    def convert(self, othercls):
        if hasattr(othercls, '__kind__'):
            config = self.report.config['report'][othercls.__kind__]
        else:
            config = {}

        return othercls(self.report, config, self.job_states, self.duration)

    @classmethod
    def get_base_config(cls, report):
        return report.config['report'][cls.mro()[-3].__kind__]

    @classmethod
    def reporter_documentation(cls):
        result = []
        for sc in TrackSubClasses.sorted_by_kind(cls):
            result.extend((
                '  * %s - %s' % (sc.__kind__, sc.__doc__),
            ))
        return '\n'.join(result)

    @classmethod
    def submit_one(cls, name, report, job_states, duration):
        subclass = cls.__subclasses__[name]
        cfg = report.config['report'].get(name, {'enabled': False})
        if cfg['enabled']:
            base_config = subclass.get_base_config(report)
            if base_config.get('separate', False):
                for job_state in job_states:
                    subclass(report, cfg, [job_state], duration).submit()
            else:
                subclass(report, cfg, job_states, duration).submit()
        else:
            raise ValueError('Reporter not enabled: {name}'.format(name=name))

    @classmethod
    def submit_all(cls, report, job_states, duration):
        any_enabled = False
        for name, subclass in cls.__subclasses__.items():
            cfg = report.config['report'].get(name, {})
            if cfg.get('enabled', False):
                any_enabled = True
                logger.info('Submitting with %s (%r)', name, subclass)
                base_config = subclass.get_base_config(report)
                if base_config.get('separate', False):
                    for job_state in job_states:
                        subclass(report, cfg, [job_state], duration).submit()
                else:
                    subclass(report, cfg, job_states, duration).submit()

        if not any_enabled:
            logger.warning('No reporters enabled.')

    def submit(self):
        raise NotImplementedError()


class SafeHtml(object):
    def __init__(self, s):
        self.s = s

    def __str__(self):
        return self.s

    def format(self, *args, **kwargs):
        return str(self).format(*(html.escape(str(arg)) for arg in args),
                                **{k: html.escape(str(v)) for k, v in kwargs.items()})


class HtmlReporter(ReporterBase):

    __kind__ = 'html'

    def submit(self):
        yield from (str(part) for part in self._parts())

    def _parts(self):
        cfg = self.get_base_config(self.report)

        yield SafeHtml("""<!DOCTYPE html>
        <html><head>
            <title>urlwatch</title>
            <meta http-equiv="content-type" content="text/html; charset=utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta name="color-scheme" content="light dark">
            <meta name="supported-color-schemes" content="light dark only">
            <style type="text/css">
                :root { color-scheme: light dark; supported-color-schemes: light dark; }
                body { font-family: sans-serif; }
                .diff_add { background-color: #abf2bc; display: inline-block; }
                .diff_sub { background-color: #ffd7d5; display: inline-block; }
                .diff_chg { background-color: #f9e48b; display: inline-block; }
                .unified_add { color: green; }
                .unified_sub { color: red; }
                .unified_nor { color: #333; }
                td, th, colgroup { border: none; }
                table, thead, tbody { border: 1px solid #9a9a9a; }
                .diff_next { border-left: 1px solid #9a9a9a; }
                td.diff_header, td.diff_next { color: #6e7781; background-color: #f5f5f5; text-align: right; vertical-align: top; }
                table { font-family: monospace; line-height: 1.5em; }
                td, th { padding: 0 0.5em; }
                td[nowrap] { width: 50%; vertical-align: top; white-space: normal; word-break: break-word; }
                h2 span.verb { color: #888; }
                @media (prefers-color-scheme: dark) {
                    body { background-color: #121212; color: #fff; }
                    a { color: #8ab5f8; }
                    a:visited { color: #c58af9; }
                    td.diff_header, td.diff_next { background-color: #1c1c1c; }
                    .diff_add { background-color: #1c4329; }
                    .diff_sub { background-color: #542527; }
                    .diff_chg { background-color: #907709; }
                    .unified_nor { color: #ddd; }
                }
            </style>
        </head><body>
        """)

        for job_state in self.report.get_filtered_job_states(self.job_states):
            job = job_state.job

            if job.location_is_url():
                title = '<a href="{location}">{pretty_name}</a>'
            elif job.pretty_name() != job.get_location():
                title = '<span title="{location}">{pretty_name}</span>'
            else:
                title = '{location}'
            title = '<h2><span class="verb">{verb}:</span> ' + title + '</h2>'

            yield SafeHtml(title).format(verb=job_state.verb,
                                         location=job.get_location(),
                                         pretty_name=job.pretty_name())

            content = self._format_content(job_state, cfg['diff'])
            if content is not None:
                yield content

            yield SafeHtml('<hr>')

        yield SafeHtml('<address>')
        for part in self.get_signature():
            yield SafeHtml('{}<br>').format(part)
        yield SafeHtml("""</address>
        </body>
        </html>
        """)

    def _diff_to_html(self, unified_diff):
        result = unified_diff
        diff_mapping = {'+': 'unified_add', '-': 'unified_sub'}

        result = re.sub(r'^([-+]).*$', lambda x: '<span class="' + diff_mapping[x.group(1)] + '">' + x.group(0) + '</span>', result, flags=re.MULTILINE)
        result = re.sub(WDIFF_ADDED_RE, lambda x: '<span class="diff_add">' + x.group(0) + '</span>', result, flags=re.MULTILINE + re.DOTALL)
        result = re.sub(WDIFF_REMOVED_RE, lambda x: '<span class="diff_sub">' + x.group(0) + '</span>', result, flags=re.MULTILINE + re.DOTALL)

        return str(SafeHtml('<span class="unified_nor">' + result + '</span>')).splitlines()

    def _format_content(self, job_state, difftype):
        if job_state.verb == 'error':
            return SafeHtml('<pre style="text-color: red;">{error}</pre>').format(error=job_state.traceback.strip())

        if job_state.verb == 'unchanged':
            return SafeHtml('<pre>{old_data}</pre>').format(old_data=job_state.old_data)

        if job_state.old_data in (None, job_state.new_data):
            return SafeHtml('...')

        if difftype == 'table':
            timestamp_old = email.utils.formatdate(job_state.timestamp, localtime=True)
            timestamp_new = email.utils.formatdate(time.time(), localtime=True)
            html_diff = difflib.HtmlDiff()
            return SafeHtml(html_diff.make_table(job_state.old_data.splitlines(keepends=True),
                                                 job_state.new_data.splitlines(keepends=True),
                                                 timestamp_old, timestamp_new, True, 3))
        elif difftype == 'unified':
            return ''.join((
                '<pre>',
                '\n'.join(self._diff_to_html(job_state.get_diff())),
                '</pre>',
            ))
        else:
            raise ValueError('Diff style not supported: %r' % (difftype,))


class TextReporter(ReporterBase):

    __kind__ = 'text'

    def submit(self):
        cfg = self.get_base_config(self.report)
        line_length = cfg['line_length']
        show_details = cfg['details']
        show_footer = cfg['footer']

        if cfg['minimal']:
            for job_state in self.report.get_filtered_job_states(self.job_states):
                pretty_name = job_state.job.pretty_name()
                location = job_state.job.get_location()
                if pretty_name != location:
                    location = '%s ( %s )' % (pretty_name, location)
                yield ': '.join((job_state.verb.upper(), location))
            return

        summary = []
        details = []
        for job_state in self.report.get_filtered_job_states(self.job_states):
            summary_part, details_part = self._format_output(job_state, line_length)
            summary.extend(summary_part)
            details.extend(details_part)

        if summary:
            sep = (line_length * '=') or None
            yield from (part for part in itertools.chain(
                (sep,),
                ('%02d. %s' % (idx, line) for idx, line in enumerate(summary, 1)),
                (sep, ''),
            ) if part is not None)

        if show_details:
            yield from details

        if summary and show_footer:
            yield '-- '
            yield from self.get_signature()

    def _format_content(self, job_state):
        if job_state.verb == 'error':
            return job_state.traceback.strip()

        if job_state.verb == 'unchanged':
            return job_state.old_data

        if job_state.old_data in (None, job_state.new_data):
            return None

        return job_state.get_diff()

    def _format_output(self, job_state, line_length):
        summary_part = []
        details_part = []

        pretty_name = job_state.job.pretty_name()
        location = job_state.job.get_location()
        if pretty_name != location:
            location = '%s ( %s )' % (pretty_name, location)

        pretty_summary = ': '.join((job_state.verb.upper(), pretty_name))
        summary = ': '.join((job_state.verb.upper(), location))
        content = self._format_content(job_state)

        summary_part.append(pretty_summary)

        sep = (line_length * '-') or None
        details_part.extend((sep, summary, sep))
        if content is not None:
            details_part.extend((content, sep))
        details_part.extend(('', '') if sep else ('',))
        details_part = [part for part in details_part if part is not None]

        return summary_part, details_part


class StdoutReporter(TextReporter):
    """Print summary on stdout (the console)"""

    __kind__ = 'stdout'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._has_color = sys.stdout.isatty() and self.config.get('color', False)

    def _incolor(self, color_id, s):
        if self._has_color:
            return '\033[9%dm%s\033[0m' % (color_id, s)
        return s

    def _red(self, s):
        return self._incolor(1, s)

    def _green(self, s):
        return self._incolor(2, s)

    def _yellow(self, s):
        return self._incolor(3, s)

    def _blue(self, s):
        return self._incolor(4, s)

    def _get_print(self):
        if sys.platform == 'win32' and self._has_color and AnsiToWin32 is not None:
            return functools.partial(print, file=AnsiToWin32(sys.stdout).stream)
        return print

    def submit(self):
        print = self._get_print()

        cfg = self.get_base_config(self.report)
        line_length = cfg['line_length']

        separators = (line_length * '=', line_length * '-', '-- ') if line_length else ()
        body = '\n'.join(super().submit())

        for line in body.splitlines():
            # Basic colorization for wdiff-style differences
            line = re.sub(WDIFF_ADDED_RE, lambda x: self._green(x.group(0)), line)
            line = re.sub(WDIFF_REMOVED_RE, lambda x: self._red(x.group(0)), line)

            # FIXME: This isn't ideal, but works for now...
            if line in separators:
                print(line)
            elif line.startswith('+'):
                print(self._green(line))
            elif line.startswith('-'):
                print(self._red(line))
            elif any(line.startswith(prefix) for prefix in ('NEW:', 'CHANGED:', 'UNCHANGED:', 'ERROR:')):
                first, second = line.split(' ', 1)
                if line.startswith('ERROR:'):
                    print(first, self._red(second))
                else:
                    print(first, self._blue(second))
            else:
                print(line)


class EMailReporter(TextReporter):
    """Send summary via e-mail / SMTP"""

    __kind__ = 'email'

    def submit(self):
        filtered_job_states = list(self.report.get_filtered_job_states(self.job_states))

        subject_args = {
            'count': len(filtered_job_states),
            'jobs': ', '.join(job_state.job.pretty_name() for job_state in filtered_job_states),
        }
        subject = self.config['subject'].format(**subject_args)

        body_text = '\n'.join(super().submit())

        if not body_text:
            logger.debug('Not sending e-mail (no changes)')
            return
        if self.config['method'] == "smtp":
            smtp_user = self.config['smtp'].get('user', None) or self.config['from']
            # Legacy support: The current smtp "auth" setting was previously called "keyring"
            if 'keyring' in self.config['smtp']:
                logger.info('The SMTP config key "keyring" is now called "auth". See https://urlwatch.readthedocs.io/en/latest/deprecated.html')
            use_auth = self.config['smtp'].get('auth', self.config['smtp'].get('keyring', False))
            mailer = SMTPMailer(smtp_user, self.config['smtp']['host'], self.config['smtp']['port'],
                                self.config['smtp']['starttls'], use_auth,
                                self.config['smtp'].get('insecure_password'))
        elif self.config['method'] == "sendmail":
            mailer = SendmailMailer(self.config['sendmail']['path'])
        else:
            logger.error('Invalid entry for method {method}'.format(method=self.config['method']))

        reply_to = self.config.get('reply_to', '')
        if self.config['html']:
            body_html = '\n'.join(self.convert(HtmlReporter).submit())

            msg = mailer.msg_html(self.config['from'], self.config['to'], reply_to, subject, body_text, body_html)
        else:
            msg = mailer.msg_plain(self.config['from'], self.config['to'], reply_to, subject, body_text)

        mailer.send(msg)


class IFTTTReport(TextReporter):
    """Send summary via IFTTT"""

    __kind__ = 'ifttt'

    def submit(self):
        webhook_url = 'https://maker.ifttt.com/trigger/{event}/with/key/{key}'.format(**self.config)
        for job_state in self.report.get_filtered_job_states(self.job_states):
            pretty_name = job_state.job.pretty_name()
            location = job_state.job.get_location()
            result = requests.post(webhook_url, json={
                'value1': job_state.verb,
                'value2': pretty_name,
                'value3': location,
            })


class WebServiceReporter(TextReporter):
    MAX_LENGTH = 1024

    __kind__ = 'webservice'

    def web_service_get(self):
        raise NotImplementedError

    def web_service_submit(self, service, title, body):
        raise NotImplementedError

    def submit(self):
        body_text = '\n'.join(super().submit())

        if not body_text:
            logger.debug('Not sending %s (no changes)', self.__kind__)
            return

        if len(body_text) > self.MAX_LENGTH:
            body_text = body_text[:self.MAX_LENGTH]

        try:
            service = self.web_service_get()
        except Exception:
            logger.error('Failed to load or connect to %s - are the dependencies installed and configured?',
                         self.__kind__, exc_info=True)
            return

        self.web_service_submit(service, 'Website Change Detected', body_text)


class PushoverReport(WebServiceReporter):
    """Send summary via pushover.net"""

    __kind__ = 'pushover'

    def web_service_get(self):
        if chump is None:
            raise ImportError('Python module "chump" not installed')

        app = chump.Application(self.config['app'])
        return app.get_user(self.config['user'])

    def web_service_submit(self, service, title, body):
        sound = self.config['sound']
        # If device is the empty string or not specified at all, use None to send to all devices
        # (see https://github.com/thp/urlwatch/issues/372)
        device = self.config.get('device', None) or None
        priority = {
            'lowest': chump.LOWEST,
            'low': chump.LOW,
            'normal': chump.NORMAL,
            'high': chump.HIGH,
            'emergency': chump.EMERGENCY,
        }.get(self.config.get('priority', None), chump.NORMAL)
        msg = service.create_message(title=title, message=body, html=True, sound=sound, device=device, priority=priority)
        msg.send()


class PushbulletReport(WebServiceReporter):
    """Send summary via pushbullet.com"""

    __kind__ = 'pushbullet'

    def web_service_get(self):
        if Pushbullet is None:
            raise ImportError('Python module "pushbullet" not installed')

        return Pushbullet(self.config['api_key'])

    def web_service_submit(self, service, title, body):
        service.push_note(title, body)


class MailGunReporter(TextReporter):
    """Send e-mail via the Mailgun service"""

    __kind__ = 'mailgun'

    def submit(self):
        region = self.config.get('region', '')
        domain = self.config['domain']
        api_key = self.config['api_key']
        from_name = self.config['from_name']
        from_mail = self.config['from_mail']
        to = self.config['to']

        if region == 'us':
            region = ''

        if region != '':
            region = ".{0}".format(region)

        filtered_job_states = list(self.report.get_filtered_job_states(self.job_states))
        subject_args = {
            'count': len(filtered_job_states),
            'jobs': ', '.join(job_state.job.pretty_name() for job_state in filtered_job_states),
        }
        subject = self.config['subject'].format(**subject_args)

        body_text = '\n'.join(super().submit())
        body_html = '\n'.join(self.convert(HtmlReporter).submit())

        if not body_text:
            logger.debug('Not calling Mailgun API (no changes)')
            return

        logger.debug("Sending Mailgun request for domain:'{0}'".format(domain))
        result = requests.post(
            "https://api{0}.mailgun.net/v3/{1}/messages".format(region, domain),
            auth=("api", api_key),
            data={"from": "{0} <{1}>".format(from_name, from_mail),
                  "to": to,
                  "subject": subject,
                  "text": body_text,
                  "html": body_html})

        try:
            json_res = result.json()

            if (result.status_code == requests.codes.ok):
                logger.info("Mailgun response: id '{0}'. {1}".format(json_res['id'], json_res['message']))
            else:
                logger.error("Mailgun error: {0}".format(json_res['message']))
        except ValueError:
            logger.error(
                "Failed to parse Mailgun response. HTTP status code: {0}, content: {1}".format(result.status_code,
                                                                                               result.content))

        return result


class TelegramReporter(TextReporter):
    """Send a message using Telegram"""
    MAX_LENGTH = 4096

    __kind__ = 'telegram'

    def submit(self):

        bot_token = self.config['bot_token']
        chat_ids = self.config['chat_id']
        chat_ids = [chat_ids] if isinstance(chat_ids, str) else chat_ids

        text = '\n'.join(super().submit())

        if not text:
            logger.debug('Not calling telegram API (no changes)')
            return

        result = None
        for chunk in chunkstring(text, self.MAX_LENGTH, numbering=True):
            for chat_id in chat_ids:
                res = self.submitToTelegram(bot_token, chat_id, chunk)
                if res.status_code != requests.codes.ok or res is None:
                    result = res

        return result

    @staticmethod
    def _format_body(text: str) -> str:
        return "```diff\n{}\n```".format(
            text.translate(str.maketrans({'`': r'\`', '\\': r'\\'})))

    def submitToTelegram(self, bot_token, chat_id, text):
        logger.debug("Sending telegram request to chat id:'{0}'".format(chat_id))

        data = {"chat_id": chat_id,
                "text": text,
                "disable_notification": self.config.get('silent', False),
                "disable_web_page_preview": True}

        if self.config.get('monospace', False):
            # all "`" and "\" characters are escaped and text is put inside
            # a markdown code block. API docs on formatting messages:
            # https://core.telegram.org/bots/api#formatting-options
            data.update({
                "text": self._format_body(text),
                "parse_mode": "MarkdownV2"
            })

        result = requests.post("https://api.telegram.org/bot{0}/sendMessage".format(bot_token), json=data)
        try:
            json_res = result.json()

            if (result.status_code == requests.codes.ok):
                logger.info("Telegram response: ok '{0}'. {1}".format(json_res['ok'], json_res['result']))
            else:
                logger.error("Telegram error: {0}".format(json_res['description']))
        except ValueError:
            logger.error(
                "Failed to parse telegram response. HTTP status code: {0}, content: {1}".format(result.status_code,
                                                                                                result.content))
        return result


class SlackReporter(TextReporter):
    """Send a message to a Slack channel"""

    __kind__ = 'slack'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_length = self.config.get('max_message_length', 40000)

    def submit(self):
        webhook_url = self.config['webhook_url']
        text = '\n'.join(super().submit())

        if not text:
            logger.debug('Not calling {} API (no changes)'.format(self.__kind__))
            return

        result = None
        for chunk in chunkstring(text, self.max_length, numbering=True):
            res = self.submit_chunk(webhook_url, chunk)
            if res.status_code != requests.codes.ok or res is None:
                result = res

        return result

    def submit_chunk(self, webhook_url, text):
        logger.debug("Sending {} request with text: {}".format(self.__kind__, text))
        post_data = {"text": text}
        result = requests.post(webhook_url, json=post_data)
        try:
            if result.status_code == requests.codes.ok:
                logger.info("{} response: ok".format(self.__kind__))
            else:
                logger.error("{} error: {}".format(self.__kind__, result.text))
        except ValueError:
            logger.error(
                "Failed to parse {} response. HTTP status code: {}, content: {}".format(self.__kind__,
                                                                                        result.status_code,
                                                                                        result.content))
        return result


class MattermostReporter(SlackReporter):
    """Send a message to a Mattermost channel"""

    __kind__ = 'mattermost'


class DiscordReporter(TextReporter):
    """Send a message to a Discord channel"""

    __kind__ = 'discord'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_length = self.config.get('max_message_length', 2000)

    def submit(self):
        webhook_url = self.config['webhook_url']
        text = '\n'.join(super().submit())

        if not text:
            logger.debug('Not calling Discord API (no changes)')
            return

        result = None
        for chunk in chunkstring(text, self.max_length, numbering=True):
            res = self.submit_to_discord(webhook_url, chunk)
            if res.status_code != requests.codes.ok or res is None:
                result = res

        return result

    def submit_to_discord(self, webhook_url, text):
        if self.config.get('colored', True):
            text = "```diff\n" + text + "```"

        if self.config.get('embed', False):
            filtered_job_states = list(self.report.get_filtered_job_states(self.job_states))

            subject_args = {
                'count': len(filtered_job_states),
                'jobs': ', '.join(job_state.job.pretty_name() for job_state in filtered_job_states),
            }

            subject = self.config['subject'].format(**subject_args)

            post_data = {
                'content': subject,
                'embeds': [{
                    'type': 'rich',
                    'description': text,
                }]
            }
        else:
            post_data = {"content": text}

        logger.debug("Sending Discord request with post_data: {0}".format(post_data))

        result = requests.post(webhook_url, json=post_data)
        try:
            if result.status_code in (requests.codes.ok, requests.codes.no_content):
                logger.info("Discord response: ok")
            else:
                logger.error("Discord error: {0}".format(result.text))
        except ValueError:
            logger.error("Failed to parse Discord response. HTTP status code: {0}, content: {1}".format(result.status_code, result.content))
        return result


class MarkdownReporter(ReporterBase):

    __kind__ = 'markdown'

    def submit(self, max_length=None):
        cfg = self.get_base_config(self.report)
        show_details = cfg['details']
        show_footer = cfg['footer']

        if cfg['minimal']:
            for job_state in self.report.get_filtered_job_states(self.job_states):
                pretty_name = job_state.job.pretty_name()
                location = job_state.job.get_location()
                if pretty_name != location:
                    location = '%s (%s)' % (pretty_name, location)
                yield '* ' + ': '.join((job_state.verb.upper(), location))
            return

        summary = []
        details = []
        for job_state in self.report.get_filtered_job_states(self.job_states):
            summary_part, details_part = self._format_output(job_state)
            summary.extend(summary_part)
            details.extend(details_part)

        if summary and show_footer:
            footer = ('--- ',) + self.get_signature()
        else:
            footer = None

        if not show_details:
            details = None

        trimmed_msg = "*Parts of the report were omitted due to message length.*\n"
        max_length -= len(trimmed_msg)

        trimmed, summary, details, footer = MarkdownReporter._render(
            max_length, summary, details, footer
        )

        if summary:
            yield from summary
            yield ''

        if show_details:
            for header, body in details:
                yield header
                yield body
                yield ''

        if trimmed:
            yield trimmed_msg

        if summary and show_footer:
            yield from footer

    @classmethod
    def _render(cls, max_length, summary=None, details=None, footer=None):
        """Render the report components, trimming them if the available length is insufficient.

        Returns a tuple (trimmed, summary, details, footer).

        The first element of the tuple indicates whether any part of the report
        was omitted due to message length. The other elements are the
        potentially trimmed report components.
        """

        # The footer/summary lengths are the sum of the length of their parts
        # plus the space taken up by newlines.
        if summary:
            summary = ['%d. %s' % (idx, line) for idx, line in enumerate(summary, 1)]
            summary_len = sum(len(part) for part in summary) + len(summary) - 1
        else:
            summary_len = 0

        if footer:
            footer_len = sum(len(part) for part in footer) + len(footer) - 1
        else:
            footer_len = 0

        if max_length is None:
            return (False, summary, details, footer)
        else:
            if summary_len > max_length:
                return (True, [], [], "")
            elif footer_len > max_length - summary_len:
                return (True, summary, [], footer[:max_length - summary_len])
            elif not details:
                return (False, summary, [], footer)
            else:
                # Determine the space remaining after taking into account
                # summary and footer.
                remaining_len = max_length - summary_len - footer_len
                headers_len = sum(len(header) for header, _ in details)

                details_trimmed = False

                # First ensure we can show all the headers.
                if headers_len > remaining_len:
                    return (True, summary, [], footer)
                else:
                    remaining_len -= headers_len

                    # Calculate approximate available length per item, shared
                    # equally between all details components.
                    body_len_per_details = remaining_len // len(details)

                    trimmed_details = []
                    unprocessed = len(details)

                    for header, body in details:
                        # Calculate the available length for the body and render it
                        avail_length = body_len_per_details - 1

                        body_trimmed, body = cls._format_details_body(body, avail_length)

                        if body_trimmed:
                            details_trimmed = True

                        if len(body) <= body_len_per_details:
                            trimmed_details.append((header, body))
                        else:
                            trimmed_details.append((header, ""))

                        # If the current item's body did not use all of its
                        # allocated space, distribute the unused space into
                        # subsequent items, unless we're at the last item
                        # already.
                        unused = body_len_per_details - len(body)
                        remaining_len -= body_len_per_details
                        remaining_len += unused
                        unprocessed -= 1

                        if unprocessed > 0:
                            body_len_per_details = remaining_len // unprocessed

                    return (details_trimmed, summary, trimmed_details, footer)

    @staticmethod
    def _format_details_body(s, max_length):
        wrapper_length = len("```diff\n\n```")

        # Message to print when the diff is too long.
        trim_message = "*diff trimmed*"
        trim_message_length = len(trim_message)

        if max_length is None or len(s) + wrapper_length <= max_length:
            return False, "```diff\n{}\n```".format(s)
        else:
            target_max_length = max_length - trim_message_length - wrapper_length
            pos = s.rfind("\n", 0, target_max_length)

            if pos == -1:
                # Just a single long line, so cut it short.
                s = s[0:target_max_length]
            else:
                # Multiple lines, cut off extra lines.
                s = s[0:pos]

            return True, "{}\n```diff\n{}\n```".format(trim_message, s)

    def _format_content(self, job_state):
        if job_state.verb == 'error':
            return job_state.traceback.strip()

        if job_state.verb == 'unchanged':
            return job_state.old_data

        if job_state.old_data in (None, job_state.new_data):
            return None

        return job_state.get_diff()

    def _format_output(self, job_state):
        summary_part = []
        details_part = []

        pretty_name = job_state.job.pretty_name()
        location = job_state.job.get_location()
        if pretty_name != location:
            location = '%s (%s)' % (pretty_name, location)

        pretty_summary = ': '.join((job_state.verb.upper(), pretty_name))
        summary = ': '.join((job_state.verb.upper(), location))
        content = self._format_content(job_state)

        summary_part.append(pretty_summary)

        if content is not None:
            details_part.append(('### ' + summary, content))

        return summary_part, details_part


class MatrixReporter(MarkdownReporter):
    """Send a message to a room using the Matrix protocol"""
    MAX_LENGTH = 16384

    __kind__ = 'matrix'

    def submit(self):
        if matrix_client is None:
            raise ImportError('Python module "matrix_client" not installed')

        homeserver_url = self.config['homeserver']
        access_token = self.config['access_token']
        room_id = self.config['room_id']

        body_markdown = '\n'.join(super().submit(MatrixReporter.MAX_LENGTH))

        if not body_markdown:
            logger.debug('Not calling Matrix API (no changes)')
            return

        client_api = matrix_client.api.MatrixHttpApi(homeserver_url, access_token)

        if Markdown is not None:
            body_html = Markdown(extras=["fenced-code-blocks", "highlightjs-lang"]).convert(body_markdown)

            client_api.send_message_event(
                room_id,
                "m.room.message",
                content={
                    "msgtype": "m.text",
                    "format": "org.matrix.custom.html",
                    "body": body_markdown,
                    "formatted_body": body_html
                }
            )
        else:
            logger.debug('Not formatting as Markdown; dependency on markdown2 not met?')
            client_api.send_message(room_id, body_markdown)


class XMPPReporter(TextReporter):
    """Send a message using the XMPP Protocol"""
    MAX_LENGTH = 262144

    __kind__ = 'xmpp'

    def submit(self):

        sender = self.config['sender']
        recipient = self.config['recipient']

        text = '\n'.join(super().submit())

        if not text:
            logger.debug('Not sending XMPP message (no changes)')
            return

        xmpp = XMPP(sender, recipient, self.config.get('insecure_password'))

        for chunk in chunkstring(text, self.MAX_LENGTH, numbering=True):
            asyncio.run(xmpp.send(chunk))


class ProwlReporter(TextReporter):
    """Send a detailed notification via prowlapp.com"""

    __kind__ = 'prowl'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def submit(self):
        api_add = 'https://api.prowlapp.com/publicapi/add'

        text = '\n'.join(super().submit())

        if not text:
            logger.debug('Not calling Prowl API (no changes)')
            return

        filtered_job_states = list(self.report.get_filtered_job_states(self.job_states))
        subject_args = {
            'count': len(filtered_job_states),
            'jobs': ', '.join(job_state.job.pretty_name() for job_state in filtered_job_states),
        }

        # 'subject' used in the config file, but the API
        # uses what might be called the subject as the 'event'
        event = self.config['subject'].format(**subject_args)

        # 'application' is prepended to the message in prowl,
        # to show the source of the notification. this too,
        # is user configurable, and may reference subject args
        application = self.config.get('application')
        if application is not None:
            application = application.format(**subject_args)
        else:
            application = '{0} v{1}'.format(urlwatch.pkgname, urlwatch.__version__)

        # build the data to post
        post_data = {
            'event': event[:1024].encode('utf8'),
            'description': text[:10000].encode('utf8'),
            'application': application[:256].encode('utf8'),
            'apikey': self.config['api_key'],
            'priority': self.config['priority']
        }

        # all set up, add the notification!
        result = requests.post(api_add, data=post_data)

        try:
            if result.status_code in (requests.codes.ok, requests.codes.no_content):
                logger.info("Prowl response: ok")
            else:
                logger.error("Prowl error: {0}".format(result.text))
        except ValueError:
            logger.error("Failed to parse Prowl response. HTTP status code: {0}, content: {1}".format(
                result.status_code, result.content))

        return result


class ShellReporter(TextReporter):
    """Pipe a message to a shell command"""

    __kind__ = 'shell'

    def submit(self):
        text = '\n'.join(super().submit()) + '\n'

        if not text:
            logger.debug('Not calling shell reporter (no changes)')
            return

        cmd = self.config['command']

        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = process.communicate(text.encode())

        if stdout and not self.config.get('ignore_stdout', False):
            logger.info('Standard output from shell reporter: {!r}'.format(stdout))

        if stderr and not self.config.get('ignore_stderr', True):
            logger.warning('Standard error output from shell reporter: {!r}'.format(stderr))

        exitcode = process.wait()
        if exitcode != 0:
            logger.error('Shell reporter {} exited with {}'.format(cmd, exitcode))


class GotifyReporter(MarkdownReporter):
    """Send a message to a gotify server"""
    MAX_LENGTH = 16 * 1024

    __kind__ = 'gotify'

    def submit(self):
        body_markdown = '\n'.join(super().submit(self.MAX_LENGTH))
        if not body_markdown:
            logger.debug('Not sending message to gotify server (no changes)')
            return

        server_url = self.config['server_url']
        url = f'{server_url}/message'

        token = self.config['token']
        headers = {'Authorization': f'Bearer {token}'}

        requests.post(url, headers=headers, json={
            "extras": {
                "client::display": {
                    "contentType": "text/markdown",
                },
            },
            'message': body_markdown,
            'priority': self.config['priority'],
            'title': self.config['title'],
        })
