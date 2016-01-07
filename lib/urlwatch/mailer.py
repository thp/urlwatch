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

import email.mime.text
import email.utils


def send(smtp_server, from_email, to_email, subject, body, tls=False, auth=False):
    msg = email.mime.text.MIMEText(body, 'plain', 'utf_8')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Date'] = email.utils.formatdate()

    if ':' in smtp_server:
        smtp_hostname, smtp_port = smtp_server.split(':')
        smtp_port = int(smtp_port)
    else:
        smtp_port = 25
        smtp_hostname = smtp_server

    s = smtplib.SMTP()
    s.connect(smtp_hostname, smtp_port)
    s.ehlo()
    if tls:
        s.starttls()
    if auth and keyring is not None:
        passwd = keyring.get_password(smtp_server, from_email)
        if passwd is None:
            raise ValueError('No password available in keyring for {}, {}'.format(smtp_server, from_email))
        s.login(from_email, passwd)
    s.sendmail(from_email, [to_email], msg.as_string())
    s.quit()


def set_password(smtp_server, from_email):
    ''' Set the keyring password for the mail connection. Interactive.'''
    if keyring is None:
        raise ImportError('keyring module missing - service unsupported')

    password = getpass.getpass(prompt='Enter password for {} using {}: '.format(from_email, smtp_server))
    keyring.set_password(smtp_server, from_email, password)
