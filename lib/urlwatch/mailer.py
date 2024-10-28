# -*- coding: utf-8 -*-
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


import smtplib
import getpass
import subprocess
import logging

try:
    import keyring
except ImportError:
    keyring = None

import email.mime.multipart
import email.mime.text
import email.utils

logger = logging.getLogger(__name__)


class Mailer(object):
    def send(self, msg):
        raise NotImplementedError

    def msg_plain(self, from_email, to_email, reply_to_email, subject, body):
        msg = email.mime.text.MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Date'] = email.utils.formatdate()
        if reply_to_email:
            msg['Reply-To'] = reply_to_email

        return msg

    def msg_html(self, from_email, to_email, reply_to_email, subject, body_text, body_html):
        msg = email.mime.multipart.MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Date'] = email.utils.formatdate()
        if reply_to_email:
            msg['Reply-To'] = reply_to_email

        msg.attach(email.mime.text.MIMEText(body_text, 'plain', 'utf-8'))
        msg.attach(email.mime.text.MIMEText(body_html, 'html', 'utf-8'))

        return msg


class SMTPMailer(Mailer):
    def __init__(self, smtp_user, smtp_server, smtp_port, tls, auth, insecure_password=None):
        self.smtp_server = smtp_server
        self.smtp_user = smtp_user
        self.smtp_port = smtp_port
        self.tls = tls
        self.auth = auth
        self.insecure_password = insecure_password

    def send(self, msg):
        s = smtplib.SMTP(self.smtp_server, self.smtp_port)
        s.ehlo()

        if self.tls:
            s.starttls()

        if self.auth:
            if self.insecure_password:
                passwd = self.insecure_password
            elif keyring is not None:
                passwd = keyring.get_password(self.smtp_server, self.smtp_user)
                if passwd is None:
                    raise ValueError('No password available in keyring for {}, {}'
                                     .format(self.smtp_server, self.smtp_user))
            else:
                raise ValueError('SMTP auth is enabled, but insecure_password is not set and keyring is not available')
            s.login(self.smtp_user, passwd)

        s.sendmail(msg['From'], msg['To'].split(','), msg.as_string(maxheaderlen=78))
        s.quit()


class SendmailMailer(Mailer):
    def __init__(self, sendmail_path):
        self.sendmail_path = sendmail_path

    def send(self, msg):
        p = subprocess.Popen([self.sendmail_path, '-oi', '-f', msg['From']] + msg['To'].split(','),
                             stdin=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             universal_newlines=True)
        result = p.communicate(msg.as_string(maxheaderlen=78))
        if p.returncode:
            logger.error('Sendmail failed with {result}'.format(result=result))


def have_password(smtp_server, from_email):
    return keyring.get_password(smtp_server, from_email) is not None


def set_password(smtp_server, from_email):
    ''' Set the keyring password for the mail connection. Interactive.'''
    if keyring is None:
        raise ImportError('keyring module missing - service unsupported')

    password = getpass.getpass(prompt='Enter password for {} using {}: '.format(from_email, smtp_server))
    keyring.set_password(smtp_server, from_email, password)
