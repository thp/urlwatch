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


import logging
import os
import platform

logger = logging.getLogger(__name__)


class TrackSubClasses(type):
    """A metaclass that stores subclass name-to-class mappings in the base class"""

    @staticmethod
    def sorted_by_kind(cls):
        return [item for _, item in sorted((it.__kind__, it) for it in cls.__subclasses__.values())]

    def __init__(cls, name, bases, namespace):
        for base in bases:
            if base == object:
                continue

            for attr in ('__required__', '__optional__'):
                if not hasattr(base, attr):
                    continue

                inherited = getattr(base, attr, ())
                new_value = tuple(namespace.get(attr, ())) + tuple(inherited)
                namespace[attr] = new_value
                setattr(cls, attr, new_value)

        for base in bases:
            if base == object:
                continue

            if hasattr(cls, '__kind__'):
                subclasses = getattr(base, '__subclasses__', None)
                if subclasses is not None:
                    logger.info('Registering %r as %s', cls, cls.__kind__)
                    subclasses[cls.__kind__] = cls
                    break
            else:
                anonymous_subclasses = getattr(base, '__anonymous_subclasses__', None)
                if anonymous_subclasses is not None:
                    logger.info('Registering %r', cls)
                    anonymous_subclasses.append(cls)
                    break

        super().__init__(name, bases, namespace)


def atomic_rename(old_filename, new_filename):
    if platform.system() == 'Windows' and os.path.exists(new_filename):
        new_old_filename = new_filename + '.bak'
        if os.path.exists(new_old_filename):
            os.remove(new_old_filename)
        os.rename(new_filename, new_old_filename)
        os.rename(old_filename, new_filename)
        if os.path.exists(new_old_filename):
            os.remove(new_old_filename)
    else:
        os.rename(old_filename, new_filename)
