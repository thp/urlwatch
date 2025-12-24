[![Unit Tests](https://github.com/thp/urlwatch/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/thp/urlwatch/actions/workflows/unit-tests.yml)
[![Packaging status](https://repology.org/badge/tiny-repos/urlwatch.svg)](https://repology.org/metapackage/urlwatch/versions)
[![PyPI version](https://badge.fury.io/py/urlwatch.svg)](https://badge.fury.io/py/urlwatch)
[![Documentation](https://readthedocs.org/projects/urlwatch/badge/?version=latest&style=flat)](https://urlwatch.readthedocs.io/en/latest/)


```
                         _               _       _       ____
              _   _ _ __| |_      ____ _| |_ ___| |__   |___ \
             | | | | '__| \ \ /\ / / _` | __/ __| '_ \    __) |
             | |_| | |  | |\ V  V / (_| | || (__| | | |  / __/
              \__,_|_|  |_| \_/\_/ \__,_|\__\___|_| |_| |_____|

                                  ... monitors webpages for you
```

urlwatch is intended to help you watch changes in webpages and get notified
(via e-mail, in your terminal or through various third party services) of any
changes. The change notification will include the URL that has changed and
a unified diff of what has changed.

## Features

- Monitor webpages, headless browser sessions, or shell commands with unified diffs
- Chain filters to extract, clean up, and normalize content before diffing
- Send notifications via console, e-mail, and many third-party services
- YAML-based configuration that is easy to version and schedule via cron

## Requirements

- Python 3.9 or newer

## Installation

Install or upgrade with a single command:

```bash
python -m pip install --upgrade urlwatch
```

For more installation details, see the source documentation:
[docs/source/installation.rst](docs/source/installation.rst).

## Quick start

1. Run `urlwatch` once to initialize data
2. Edit jobs and filters: `urlwatch --edit` (writes `urls.yaml`)
3. Edit settings and reporters: `urlwatch --edit-config` (writes `urlwatch.yaml`)
4. Add `urlwatch` to cron (e.g., `crontab -e`) to run on a schedule

## Documentation and links

- Documentation: https://urlwatch.readthedocs.io/
- Documentation (source): [docs/source/index.rst](docs/source/index.rst)
- Website: https://thp.io/2008/urlwatch/
- E-Mail: m@thp.io
