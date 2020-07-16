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


import difflib
import re
import email.utils
import itertools
import logging
import sys
import time
import html
import functools

import requests

import urlwatch
from .mailer import SMTPMailer
from .mailer import SendmailMailer
from .util import TrackSubClasses

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
    # markdown2 is an optional dependency which provides better formatting for html and Matrix reporters.
    from markdown2 import Markdown
except ImportError:
    Markdown = None

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

    def convert(self, othercls):
        if hasattr(othercls, '__kind__'):
            config = self.report.config['report'][othercls.__kind__]
        else:
            config = {}

        return othercls(self.report, config, self.job_states, self.duration)

    @classmethod
    def reporter_documentation(cls):
        result = []
        for sc in TrackSubClasses.sorted_by_kind(cls):
            result.extend((
                '  * %s - %s' % (sc.__kind__, sc.__doc__),
            ))
        return '\n'.join(result)

    @classmethod
    def submit_all(cls, report, job_states, duration):
        any_enabled = False
        for name, subclass in cls.__subclasses__.items():
            cfg = report.config['report'].get(name, {'enabled': False})
            if cfg['enabled']:
                any_enabled = True
                logger.info('Submitting with %s (%r)', name, subclass)
                subclass(report, cfg, job_states, duration).submit()

        if not any_enabled:
            logger.warn('No reporters enabled.')

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
    def submit(self):
        yield from (str(part) for part in self._parts())

    def _parts(self):
        cfg = self.report.config['report']['html']

        yield SafeHtml("""
            <!DOCTYPE html>
            <html>
            <head>
            <title>urlwatch</title>
            <meta http-equiv="content-type" content="text/html; charset=utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body>""")

        for job_state in self.report.get_filtered_job_states(self.job_states):
            job = job_state.job

            if job.LOCATION_IS_URL:
                title = '<a href="{location}">{pretty_name}</a>'
            elif job.pretty_name() != job.get_location():
                title = '<span title="{location}" style="color:#888888">{pretty_name}</span>'
            else:
                title = '{location}'
            title = '<h2><span style="color:#888888">{verb}:</span> ' + title + '</h2>'

            yield SafeHtml(title).format(verb=job_state.verb.title(),
                                         location=job.get_location(),
                                         pretty_name=job.pretty_name())

            content = self._format_content(job_state, cfg['diff'])
            if content is not None:
                yield content

            yield SafeHtml('<hr>')

        yield SafeHtml("""
            <div style="font-family:monospace;font-style:italic">
            <span>{pkgname} {version}, {copyright}</span>
            <address>Website: <a href="{url}">{url}</a></address>
            <span>Watched {count} URLs in {duration} seconds</span>
            </div>
            </body>
            </html>""").format(pkgname=urlwatch.pkgname, version=urlwatch.__version__, copyright=urlwatch.__copyright__,
                                url=urlwatch.__url__, count=len(self.job_states), duration=self.duration.seconds)

    def _diff_to_html(self, unified_diff, is_markdown=False):
        if is_markdown and Markdown:
            # rebuild html from markdown using markdonw2 library's Markdown
            markdowner = Markdown(safe_mode='escape', extras=['strike', 'target-blank-links'])
            atags = re.compile(r'<a ')
            htags = re.compile(r'<(/?)h\d>')
            tags = re.compile(r'^<p>(<code>)?|(</code>)?</p>$')

            def mark_to_html(text):
                '''converts Markdown (as generated by pyhtml2text filter) back to html'''
                if text == '* * *':  # manually expand horizontal ruler since <hr> tag is used by us to separate jobs
                    return '-' * 80
                pre = ''
                if text.lstrip().startswith('* '):  # item of unordered list
                    lstripped = text.lstrip()
                    indent = len(text) - len(lstripped)
                    pre = '&nbsp;' * indent
                    pre += '● ' if indent == 2 else '◾ ' if indent == 4 else '○ '
                    text = text.split('* ', 1)[1]
                elif text.startswith(' '):  # replace leading spaces or converter will strip
                    lstripped = text.lstrip()
                    text = '&nbsp;' * (len(text) - len(lstripped)) + lstripped
                html_out = markdowner.convert(text).strip('\n')  # convert markdown to html
                html_out = atags.sub('<a style="font-family:inherit;color:inherit" ', html_out)  # fix <a> tag styling
                html_out, sub = tags.subn('', html_out)  # remove added tags
                if sub:
                    return pre + html_out
                html_out = htags.sub(r'<\g<1>strong>', html_out)  # replace heading tags with <strong>
                return pre + html_out

            for line in unified_diff.splitlines():
                if line[0] == '+':
                    yield '<span style="color:green">+{html}</span>'.format(html=mark_to_html(line[1:]))
                elif line[0] == '-':
                    yield '<span style="color:red">-{html}</span>'.format(html=mark_to_html(line[1:]))
                elif line[0] == '@':
                    yield '<span style="background-color:whitesmoke">+{line}</span>'.format(line=line)
                else:
                    yield line[0] + mark_to_html(line[1:])
        else:
            for line in unified_diff.splitlines():
                if line[0] == '+':
                    yield SafeHtml('<span style="color:green">{line}</span>').format(line=line)
                elif line[0] == '-':
                    yield SafeHtml('<span style="color:red">{line}</span>').format(line=line)
                elif line[0] == '@':
                    yield SafeHtml('<span style="background-color:whitesmoke">{line}</span>').format(line=line)
                else:
                    yield SafeHtml('{line}').format(line=line)

    def _format_content(self, job_state, difftype):
        if job_state.verb == 'error':
            return SafeHtml('<pre style="white-space:pre-wrap;color:red;">{error}</pre>').format(error=job_state.traceback.strip())

        if job_state.verb == 'unchanged':
            return SafeHtml('<pre style="white-space:pre-wrap">{old_data}</pre>').format(old_data=job_state.old_data)

        if job_state.old_data in (None, job_state.new_data):
            return SafeHtml('...')

        if difftype == 'unified':
            # Style should include 'padding-left:2.3em;text-indent:-2.3em' to have hanging indents of long lines
            # but Gmail strips the 'text-indent:-2.3em' and end up with everything indented
            return ''.join((
                '<pre style="white-space:pre-wrap">',
                '\n'.join(self._diff_to_html(job_state.get_diff())),
                '</pre>',
            ))
        elif difftype == 'table':
            timestamp_old = email.utils.formatdate(job_state.timestamp, localtime=1)
            timestamp_new = email.utils.formatdate(time.time(), localtime=1)
            html_diff = difflib.HtmlDiff()
            table = html_diff.make_table(job_state.old_data.splitlines(keepends=True),
                                         job_state.new_data.splitlines(keepends=True),
                                         timestamp_old, timestamp_new, True, 3)
            table = table.replace('<th ', '<th style="font-family:monospace" ')
            table = table.replace('<td ', '<td style="font-family:monospace" ')
            table = table.replace(' nowrap="nowrap"', '')
            table = table.replace('<a ', '<a style="font-family:monospace;color:inherit" ')
            table = table.replace('<span class="diff_add"', '<span style="color:green;background-color:lightgreen"')
            table = table.replace('<span class="diff_sub"', '<span style="color:red;background-color:lightred"')
            table = table.replace('<span class="diff_chg"', '<span style="color:orange;background-color:lightyellow"')
            return table
        else:
            raise ValueError('Diff style not supported: %r' % (difftype,))


class TextReporter(ReporterBase):
    def submit(self):
        cfg = self.report.config['report']['text']
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
                ('%02d. %s' % (idx + 1, line) for idx, line in enumerate(summary)),
                (sep, ''),
            ) if part is not None)

        if show_details:
            yield from details

        if summary and show_footer:
            yield from ('-- ',
                        '%s %s, %s' % (urlwatch.pkgname, urlwatch.__version__, urlwatch.__copyright__),
                        'Website: %s' % (urlwatch.__url__,),
                        'watched %d URLs in %d seconds' % (len(self.job_states), self.duration.seconds))

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
        if sys.platform == 'win32' and self._has_color:
            from colorama import AnsiToWin32
            return functools.partial(print, file=AnsiToWin32(sys.stdout).stream)
        return print

    def submit(self):
        print = self._get_print()

        cfg = self.report.config['report']['text']
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
                logger.info('The SMTP config key "keyring" is now called "auth".')
            use_auth = self.config['smtp'].get('auth', self.config['smtp'].get('keyring', False))
            mailer = SMTPMailer(smtp_user, self.config['smtp']['host'], self.config['smtp']['port'],
                                self.config['smtp']['starttls'], use_auth,
                                self.config['smtp'].get('insecure_password'))
        elif self.config['method'] == "sendmail":
            mailer = SendmailMailer(self.config['sendmail']['path'])
        else:
            logger.error('Invalid entry for method {method}'.format(method=self.config['method']))

        if self.config['html']:
            body_html = '\n'.join(self.convert(HtmlReporter).submit())

            msg = mailer.msg_html(self.config['from'], self.config['to'], subject, body_text, body_html)
        else:
            msg = mailer.msg_plain(self.config['from'], self.config['to'], subject, body_text)

        mailer.send(msg)


class WebServiceReporter(TextReporter):
    MAX_LENGTH = 1024

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
        msg = service.create_message(title=title, message=body, html=True, sound=sound, device=device)
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
    """Custom email reporter that uses Mailgun"""

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
    """Custom Telegram reporter"""
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
        for chunk in self.chunkstring(text, self.MAX_LENGTH):
            for chat_id in chat_ids:
                res = self.submitToTelegram(bot_token, chat_id, chunk)
                if res.status_code != requests.codes.ok or res is None:
                    result = res

        return result

    def submitToTelegram(self, bot_token, chat_id, text):
        logger.debug("Sending telegram request to chat id:'{0}'".format(chat_id))
        result = requests.post(
            "https://api.telegram.org/bot{0}/sendMessage".format(bot_token),
            data={"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"})
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

    def chunkstring(self, string, length):
        return (string[0 + i:length + i] for i in range(0, len(string), length))


class SlackReporter(TextReporter):
    """Custom Slack reporter"""
    MAX_LENGTH = 40000

    __kind__ = 'slack'

    def submit(self):
        webhook_url = self.config['webhook_url']
        text = '\n'.join(super().submit())

        if not text:
            logger.debug('Not calling slack API (no changes)')
            return

        result = None
        for chunk in self.chunkstring(text, self.MAX_LENGTH):
            res = self.submit_to_slack(webhook_url, chunk)
            if res.status_code != requests.codes.ok or res is None:
                result = res

        return result

    def submit_to_slack(self, webhook_url, text):
        logger.debug("Sending slack request with text:{0}".format(text))
        post_data = {"text": text}
        result = requests.post(webhook_url, json=post_data)
        try:
            if result.status_code == requests.codes.ok:
                logger.info("Slack response: ok")
            else:
                logger.error("Slack error: {0}".format(result.text))
        except ValueError:
            logger.error(
                "Failed to parse slack response. HTTP status code: {0}, content: {1}".format(result.status_code,
                                                                                             result.content))
        return result

    def chunkstring(self, string, length):
        return (string[0 + i:length + i] for i in range(0, len(string), length))


class MarkdownReporter(ReporterBase):
    def submit(self):
        cfg = self.report.config['report']['markdown']
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

        if summary:
            yield from ('%d. %s' % (idx + 1, line) for idx, line in enumerate(summary))
            yield ''

        if show_details:
            yield from details

        if summary and show_footer:
            yield from ('--- ',
                        '%s %s, %s  ' % (urlwatch.pkgname, urlwatch.__version__, urlwatch.__copyright__),
                        'Website: %s  ' % (urlwatch.__url__,),
                        'watched %d URLs in %d seconds' % (len(self.job_states), self.duration.seconds))

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

        details_part.append('### ' + summary)
        if content is not None:
            details_part.extend(('', '```', content, '```', ''))
        details_part.extend(('', ''))

        return summary_part, details_part


class MatrixReporter(MarkdownReporter):
    """Custom Matrix reporter"""
    MAX_LENGTH = 4096

    __kind__ = 'matrix'

    def submit(self):
        if matrix_client is None:
            raise ImportError('Python module "matrix_client" not installed')

        homeserver_url = self.config['homeserver']
        access_token = self.config['access_token']
        room_id = self.config['room_id']

        body_markdown = '\n'.join(super().submit())

        if not body_markdown:
            logger.debug('Not calling Matrix API (no changes)')
            return

        if len(body_markdown) > self.MAX_LENGTH:
            body_markdown = body_markdown[:self.MAX_LENGTH]

        client_api = matrix_client.api.MatrixHttpApi(homeserver_url, access_token)

        if Markdown is not None:
            body_html = Markdown().convert(body_markdown)

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
