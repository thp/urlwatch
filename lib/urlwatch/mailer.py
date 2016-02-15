# -*- coding: utf-8 -*-
#
# This file is part of urlwatch (https://thp.io/2008/urlwatch/).
# Copyright (c) 2008-2016 Thomas Perl <thp.io/about>
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

try:
    import keyring
except ImportError:
    keyring = None

import email.mime.multipart
import email.mime.text
import email.utils


class Mailer(object):
    def __init__(self, smtp_server, smtp_port, tls, auth):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.tls = tls
        self.auth = auth

    def send(self, msg):
        s = smtplib.SMTP(self.smtp_server, self.smtp_port)
        s.ehlo()

        if self.tls:
            s.starttls()

        if self.auth and keyring is not None:
            passwd = keyring.get_password(self.smtp_server, msg['From'])
            if passwd is None:
                raise ValueError('No password available in keyring for {}, {}'.format(self.smtp_server, msg['From']))
            s.login(msg['From'], passwd)

        s.sendmail(msg['From'], [msg['To']], msg.as_string())
        s.quit()

    def msg_plain(self, from_email, to_email, subject, body):
        msg = email.mime.text.MIMEText(body, 'plain', 'utf_8')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Date'] = email.utils.formatdate()

        return msg

    def msg_html(self, from_email, to_email, subject, body_text, body_html):
        msg = email.mime.multipart.MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Date'] = email.utils.formatdate()

        msg.attach(email.mime.text.MIMEText(body_text, 'plain', 'utf_8'))
        msg.attach(email.mime.text.MIMEText(body_html, 'html', 'utf_8'))

        return msg


def set_password(smtp_server, from_email):
    ''' Set the keyring password for the mail connection. Interactive.'''
    if keyring is None:
        raise ImportError('keyring module missing - service unsupported')

    password = getpass.getpass(prompt='Enter password for {} using {}: '.format(from_email, smtp_server))
    keyring.set_password(smtp_server, from_email, password)
