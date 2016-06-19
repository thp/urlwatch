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
import os
import shutil
import subprocess
import imp
from .jobs import JobBase
from .filters import FilterBase
from .reporters import ReporterBase
from .storage import UrlsYaml


def edit_yaml(yaml_file, parser, example_file=None):
    editor = os.environ.get('EDITOR', None)
    if editor is None:
        editor = os.environ.get('VISUAL', None)
    if editor is None:
        print('Please set $VISUAL or $EDITOR.')
        return 1

    fn_base, fn_ext = os.path.splitext(yaml_file)
    yaml_edit = fn_base + '.edit' + fn_ext
    try:
        if os.path.exists(yaml_file):
            shutil.copy(yaml_file, yaml_edit)
        elif example_file is not None:
            shutil.copy(example_file, yaml_edit)
        subprocess.check_call([editor, yaml_edit])
        # Check if we can still parse it
        if parser is not None:
            parser(yaml_edit).load()
        os.rename(yaml_edit, yaml_file)
        print('Saving edit changes in', yaml_file)
    except Exception as e:
        print('Parsing failed:')
        print('======')
        print(e)
        print('======')
        print('')
        print('The file', yaml_file, 'was NOT updated.')
        print('Your changes have been saved in', yaml_edit)
        return 1

    return 0


def edit_hooks(hooks_file, example_file):
    editor = os.environ.get('EDITOR', None)
    if editor is None:
        editor = os.environ.get('VISUAL', None)
    if editor is None:
        print('Please set $VISUAL or $EDITOR.')
        return 1

    fn_base, fn_ext = os.path.splitext(hooks_file)
    hooks_edit = fn_base + '.edit' + fn_ext
    try:
        if os.path.exists(hooks_file):
            shutil.copy(hooks_file, hooks_edit)
        else:
            shutil.copy(example_file, hooks_edit)
        subprocess.check_call([editor, hooks_edit])
        imp.load_source('hooks', hooks_edit)
        os.rename(hooks_edit, hooks_file)
        print('Saving edit changes in', hooks_file)
    except Exception as e:
        print('Parsing failed:')
        print('======')
        print(e)
        print('======')
        print('')
        print('The file', hooks_file, 'was NOT updated.')
        print('Your changes have been saved in', hooks_edit)
        return 1

    return 0


def show_features():
    print()
    print('Supported jobs:\n')
    print(JobBase.job_documentation())

    print('Supported filters:\n')
    print(FilterBase.filter_documentation())
    print()
    print('Supported reporters:\n')
    print(ReporterBase.reporter_documentation())
    print()
    return 0


def list_urls(jobs, verbose):
    for idx, job in enumerate(jobs):
        if verbose:
            print('%d: %s' % (idx + 1, repr(job)))
        else:
            pretty_name = job.pretty_name()
            location = job.get_location()
            if pretty_name != location:
                print('%d: %s (%s)' % (idx + 1, pretty_name, location))
            else:
                print('%d: %s' % (idx + 1, pretty_name))
    return 0


def modify_urls(jobs, urls, add, delete):
    save = True
    if delete is not None:
        try:
            index = int(delete) - 1
            try:
                job = jobs.pop(index)
                print('Removed %r' % (job,))
            except IndexError:
                print('Not found: %r' % (index,))
                save = False
        except ValueError:
            job = next((job for job in jobs if job.get_location() == delete), None)
            try:
                jobs.remove(job)
                print('Removed %r' % (job,))
            except ValueError:
                print('Not found: %r' % (delete,))
                save = False

    if add is not None:
        d = {k: v for k, v in (item.split('=', 1) for item in add.split(','))}
        job = JobBase.unserialize(d)
        print('Adding %r' % (job,))
        jobs.append(job)

    if save:
        print('Saving updated list to %r' % (urls,))
        UrlsYaml(urls).save(jobs)

    return 0