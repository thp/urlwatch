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

import asyncio
import getpass

try:
    import keyring
except ImportError:
    keyring = None

try:
    import aioxmpp
except ImportError:
    aioxmpp = None


class XMPP(object):
    def __init__(self, sender, recipient, insecure_password=None):
        if aioxmpp is None:
            raise ImportError('Python module "aioxmpp" not installed')

        self.sender = sender
        self.recipient = recipient
        self.insecure_password = insecure_password

    async def send(self, chunk):
        if self.insecure_password:
            password = self.insecure_password
        elif keyring is not None:
            password = keyring.get_password("urlwatch_xmpp", self.sender)
            if password is None:
                raise ValueError(
                    "No password available in keyring for {}".format(self.sender)
                )

        jid = aioxmpp.JID.fromstr(self.sender)
        client = aioxmpp.PresenceManagedClient(
            jid, aioxmpp.make_security_layer(password)
        )
        recipient_jid = aioxmpp.JID.fromstr(self.recipient)

        async with client.connected() as stream:
            msg = aioxmpp.Message(to=recipient_jid, type_=aioxmpp.MessageType.CHAT,)
            msg.body[None] = chunk

            await stream.send_and_wait_for_sent(msg)


def xmpp_have_password(sender):
    return keyring.get_password("urlwatch_xmpp", sender) is not None


def xmpp_set_password(sender):
    """ Set the keyring password for the XMPP connection. Interactive."""
    if keyring is None:
        raise ImportError("keyring module missing - service unsupported")

    password = getpass.getpass(prompt="Enter password for {}: ".format(sender))
    keyring.set_password("urlwatch_xmpp", sender, password)
