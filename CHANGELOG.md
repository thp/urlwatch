# Changelog

All notable changes to this project will be documented in this file.

The format mostly follows [Keep a Changelog](http://keepachangelog.com/en/1.0.0/).

## [UNRELEASED]

### Added

- The Telegram reporter has gained two new options:
  - `silent`: Receive message notification without sound
  - `monospace`: Format message in monospace style

### Changed

- Migrated CI pipeline from Travis CI to Github Actions

## [2.23] -- 2021-04-10

### Added

- New filter: `pretty-xml` to indent/pretty-print XML documents
- New filter: `jq` to parse, transform, and extract JSON data
- New reporter: `prowl` (by nitz)

### Fixed

- Proper multi-line highlighting for wdiff (PR#615, by kongomongo)
- Fix command-line generation for html2text (PR#619, by Eloy Paris)

## [2.22] -- 2020-12-19

### Added

- Added 'wait_until' option to browser jobs to configure how long
  the headless browser will wait for pages to load.
- Jobs now have an optional `treat_new_as_changed` (default `false`)
  key that can be set, and will treat newly-found pages as changed,
  and display a diff from the empty string (useful for `diff_tool`
  or `diff_filter` with side effects)
- New reporters: `discord`, `mattermost`
- New key `user_visible_url` for URL jobs that can be used to show
  a different URL in reports (useful if the watched URL is a REST API
  endpoint, but the report should link to the corresponding web page)
- The Markdown reporter now supports limiting the report length via the
  `max_length` parameter of the `submit` method. The length limiting logic is
  smart in the sense that it will try trimming the details first, followed by
  omitting them completely, followed by omitting the summary. If a part of the
  report is omitted, a note about this is added to the report. (PR#572, by
  Denis Kasak)

### Changed

- Diff output is now generated more uniformly, independent of whether
  the input data has a trailing newline or not; if this behavior is not
  intended, use an external `diff_tool` (PR#550, by Adam Goldsmith)
- The `--test-diff-filter` output now properly reports timestamps from
  the history entry instead of the current date and time (Fixes #573)
- Unique GUIDs for jobs are now enforced at load time, append "#1",
  "#2", ... to the URLs to make them unique if you have multiple
  different jobs that share the same request URL (Fixes #586)
- When a config, urls file or hooks file does not exist and should be
  edited or inited, its parent folders will be created (previously
  only the urlwatch configuration folder was created; Fixes #594)
- Auto-matched filters now always get `None` supplied as subfilter;
  any custom filters must accept a `subfilter` parameter after the
  existing `data` parameter
- Drop support for Python 3.5

## Fixed

- Make imports thread-safe: This might increase startup times a bit,
  as dependencies are imported on bootup instead of when first used.
  Importing in Python is not (yet) thread-safe, so we cannot import
  new modules from the worker threads reliably (Fixes #559, #601)

- The Matrix reporter was improved in several ways (PR#572, by Denis Kasak):

  - The maximum length of the report was increase from 4096 to 16384.
  - The report length limiting is now implemented via the new length limiting
    functionality of the Markdown reporter. Previously, the report was simply
    trimmed at the end which could break the diff blocks and make them render
    incorrectly.
  - The diff code blocks are now tagged as diffs which will allow the diffs to
    be syntax highlighted as such. This doesn't yet work in Element, pending on
    the resolution of trentm/python-markdown2#370.

## [2.21] -- 2020-07-31

### Added

- Added `--test-reporter REPORTER` command-line option to send an
  example report using any configured notification service
- `JobBase` now has `main_thread_enter()` and `main_thread_exit()`
  functions that can be overridden by subclasses to run code in
  the main thread before and after processing of a job
  (based on an initial implementation by Chenfeng Bao)

### Removed

- The `--test-slack` command line option has been removed, you can
  test your Slack reporter configuration using `--test-reporter slack`

### Changed

- The `browser` job now uses Pyppeteer instead of Requests-HTML for
  rendering pages while executing JavaScript; this makes JavaScript
  execution work properly (based on code by Chenfeng Bao)

### Fixed

- Applying legacy `hooks.py` filters (broken since 2.19; reported by Maxime Werlen)


## [2.20] -- 2020-07-29

### Added

- A job can now have a `diff_filter` set, which works the same way as the normal
  `filter` (and has the same filters available), but applies to the `diff` output
  instead of the page content (can be tested with `--test-diff-filter`, needs 2
  or more historic snapshots in the cache)
- Documentation now has a section on the configuration settings (`--edit-config`)
- New filter: ``ocr`` to convert text in images to plaintext (using Tesseract OCR)
- New reporters:
  - ``ifttt`` to send an event to If This Then That (ifttt.com) (#512, by Florian Gaultier)
  - ``xmpp`` to send a message using the XMPP (Jabber) protocol (#533, by Thorben Günther)

### Changed

- The `urlwatch` script (Git only) now works when run from different paths
- Chunking of strings (e.g. for Slack and Telegram) now adds numbering (e.g.
  ` (1/2)`) to the messages (only if a message is split into multiple parts)
- Unit tests have been migrated from `nose` to `pytest`
  and moved from `test/` to `lib/urlwatch/tests/`
- The ``css`` and ``xpath`` filters now accept ``skip`` and ``maxitems`` as subfilter
- The ``shellpipe`` filter now inherits all environment variables (e.g. ``$PATH``)
  of the ``urlwatch`` process

### Fixed

- The ``html2text`` method ``lynx`` now treats any subfilters with a non-``null``
  value as command-line argument ``-key value`` (previously only the value ``true``
  was treated like this, and any other values were silently dropped)


## [2.19] -- 2020-07-17

### Added

- Documentation is now available at [urlwatch.readthedocs.io](https://urlwatch.readthedocs.io)
  and shipped in the source tarball under `docs/`; filter examples in the docs are unit-tested
- New filters:
  - `reverse`: Reverse input items (default: line-based) with optional `separator`
  - `pdf2text`: Convert PDF files to plaintext (must be first filter in chain)
  - `shellpipe`: Filter text with arbitrary command-line utilities / shell scripts
- `FilterBase` API improvements for specifying subfilters:
  - Add `__supported_subfilters__` for sub filter checking and `--features` output
  - Add `__default_subfilter__` to map value-only parameters to dict parameters,
    for example the `grep` filter now has a default subfilter named `re`
- Support for using Redis as a cache backend via `--cache=redis://localhost:6379/`

### Fixed

- Declare updated Python 3.5 dependency in `setup.py` (already a requirement since urlwatch 2.18)

### Changed

- Filter improvements:
  - `sort`: Add `reverse` option to reverse the sorting order
  - `sort`: Add `separator` option to specify item separator (default is still line-based)
  - `beautify`: The `jsbeautifier` (for `<script>` tags) and `cssbeautifier` (for `<style>` tags)
    module dependencies are now optional - if they are not installed, beautify only works on the HTML
  - Most filters that only had unnamed subfilters (e.g. `grep`) now have a named default subfilter
- Reporter improvements:
  - ``pushover``: The message ``priority`` can now be configured
- Travis CI: Set `pycodestyle` version to 2.6.0 to avoid CI breakage when new style checks are added
- Diff results are now runtime cached on a per-job basis, which shouldn't affect behavior, but
  could be observed by an external `diff_tool` running at most once per job instead of multiple times
- Jobs with a custom `diff_tool` or a `shellpipe` filter are now ignored if `jobs.yaml` has the
  world-writable bit (`o+w`) set or is not owned by the current user (does not apply to Windows);
  previously only `shell` jobs were ignored if the permissions/owners were wrong

### Deprecated

- String-based filter definitions (e.g. `html2text,grep:Current.*version,strip`) are now
  deprecated, it is recommended to use YAML-based dictionary-style listing of filters,
  which is more flexible, easier to read and write and more structured


## [2.18] -- 2020-05-03

### Added
- New filter: `re.sub` that can replace/remove strings using regular expressions
- Support `ignore_timeout_errors` and `ignore_too_many_redirects` for URL jobs (#423, by Josh aka Zevlag)
- HTML reporter: Add `viewport` meta tag for improved viewing on mobile devices (#432, by Mike Borsetti)
- Optional support for insecure SMTP password storage in the config; use with caution (#431)
- Add `matrix` reporter
- New filter: `beautify` that can beautify HTML, JavaScript and CSS

### Fixed
- Fix `--test-filter` when the specified job is not found
- Fix another `YAMLLoadWarning` in unit tests (#382, by Louis Sautier)
- Documentation updates and typo fixes (by Nate Eagleson)
- Pushover: Fix default device config (Fixes #409 and #372, documented by Richard Goodwin)

### Changed
- Nicer formatting of `--features` for jobs with no docstring or many keys
- The XPath and CSS filters now support XML namespaces (#404, by Chenfeng Bao)
- Drop support for Python 3.3 and Python 3.4 (new minimum requirement is Python 3.5)
- Use `html.escape` instead of `cgi.escape` (which was removed in Python 3.8; #424, by Chenfeng Bao)
- Allow non-ASCII characters in `format-json` output filter (#433, by Mike Borsetti)
- The `keyring` config option for `email` was changed to `auth`; if you have problems
  with authentication where none is needed, set `report/email/smtp/auth` to `false`


## [2.17] -- 2019-04-12

### Added
- XPath/CSS: Support for excluding elements (#333, by Chenfeng Bao)
- Add support for using external `diff_tool` on Windows (#373, by Chenfeng Bao)
- Document how to use Amazon Simple E-Mail Service "SES" (by mborsetti)
- Compare data with multiple old versions (`compared_versions`, #328, by Chenfeng Bao)

### Fixed
- YAML: Fix deprecation warnings (#367, by Florent Aide)
- Updated manpage with new options: Authentication, filter tests (Fixes #351)
- Text formatter: Do not emit empty lines for `line_length=0` (Fixes #357)

### Changed
- SMTP configuration fix: Only use smtp.user config if it's a non-empty value


## [2.16] -- 2019-01-27

### Added
- XPath: Handle `/text()` selector (#282)
- Document how to specify cookies to README.md (#264)
- Text Reporter: `minimal` config option to only print a summary (PR#304, fixes #147)
- README.md: Document how to watch Github releases via XPath (#266)
- Support for parsing XML/RSS with XPath (Fixes #281)
- Allow explicit setting of `encoding` for URL jobs (PR#313, contributes to #306)
- Slack Channel Reporter (PR#309)
- ANSI color output on the Windows console via `colorama` (PR#296, closes #295)
- Support for using CSS selectors via the `cssselect` module (PR#321, closes 273)
- `ignore_http_error_codes` is now an option for URL jobs (PR#325, fixes #203)
- `job_defaults` in the config for globally specifying settings (PR#345, closes #253)
- Optional `timeout` (in seconds) for URL jobs to specify socket timeout (PR#348, closes #340)

### Removed
- Support for JSON storage (dead code that was never used in production; PR#336)

### Changed
- `HtmlReporter` now also highlights links for browser jobs (PR#303)
- Allow `--features` and `--edit-*` to run without `urls.yaml` (PR#301)
- When a previous run had errors, do not use conditional GETs (PR#313, fixes #292)
- Explicitly specify JSON pretty print `separators` for consistency (PR#343)
- Use data-driven unit tests/fixtures for easier unit test maintenance (PR#344)

### Fixed
- Fix migration issues with case-insensitive filesystems (#223)
- Correctly reset retry counter when job is added or unchanged (PR#291, PR#314)
- Fix a `FutureWarning` on Python 3.7 with regard to regular expressions (PR#299)
- If the filter list is empty, do not process the filter list (PR#308)
- Fix parsing/sanity-checking of `urls.yaml` after editing (PR#317, fixes #316)
- Fix Python 3.3 compatibility by depending on `enum34` there (PR#311)
- Allow running unit tests on Windows (PR#318)
- Fix migration issues introduced by PR#180 and #256 (PR#323, fixes #267)


## [2.15] -- 2018-10-23

### Added
- Support for Mailgun regions (by Daniel Peukert, PR#280)
- CLI: Allow multiple occurrences of 'filter' when adding jobs (PR#278)

### Changed
- Fixed incorrect name for chat_id config in the default config (by Robin B, PR#276)


## [2.14] -- 2018-08-30

### Added
- Filter to pretty-print JSON data: `format-json` (by Niko Böckerman, PR#250)
- List active Telegram chats using `--telegram-chats` (with fixes by Georg Pichler, PR#270)
- Support for HTTP `ETag` header in URL jobs and `If-None-Match` (by Karol Babioch, PR#256)
- Support for filtering HTML using XPath expressions, with `lxml` (PR#274, Fixes #226)
- Added `install_dependencies` to `setup.py` commands for easy installing of dependencies
- Added `ignore_connection_errors` per-job configuration option (by Karol Babioch, PR#261)

### Changed
- Improved code (HTTP status codes, by Karol Babioch PR#258)
- Improved documentation for setting up Telegram chat bots
- Allow multiple chats for Telegram reporting (by Georg Pichler, PR#271)


## [2.13] -- 2018-06-03

### Added
- Support for specifying a `diff_tool` (e.g. `wdiff`) for each job (Fixes #243)
- Support for testing filters via `--test-filter JOB` (Fixes #237)

### Changed
- Moved ChangeLog file to CHANGELOG.md and using Keep a Changelog format.
- Force version check in `setup.py`, to exclude Python 2 (Fixes #244)
- Remove default parameter from internal `html2text` module (Fixes #239)
- Better error/exception reporting in `--verbose` mode (Fixes #164)

### Removed
- Old ChangeLog entries


## [2.12] -- 2018-06-01

### Fixed
- Bugfix: Do not 'forget' old data if an exception occurs (Fixes #242)


## [2.11] -- 2018-05-19

### Fixed
- Retry: Make sure `tries` is initialized to zero on load (Fixes #241)

### Changed
- html2text: Make sure the bs4 method strips HTML tags (by Louis Sautier)


## [2.10] -- 2018-05-17

### Added
- Browser: Add support for browser jobs using `requests-html` (Fixes #215)
- Retry: Add support for optional retry count in job list (by cmichi, fixes #235)
- HTTP: Add support for specifying optional headers (by Tero Mononen)

### Changed
- File editing: Fix issue when `$EDITOR` contains spaces (Fixes #220)
- ChangeLog: Add versions to recent ChangeLog entries (Fixes #235)


## [2.9] -- 2018-03-24

### Added
- E-Mail: Add support for `--smtp-login` and document GMail SMTP usage
- Pushover: Device and sound attribute (by Tobias Haupenthal)

### Changed
- XDG: Move cache file to `XDG_CACHE_DIR` (by Maxime Werlen)
- Migration: Unconditionally migrate urlwatch 1.x cache dirs (Fixes #206)

### Fixed
- Cleanups: Fix out-of-date debug message, use https (by Jakub Wilk)


## [2.8] -- 2018-01-28

### Changed
- Documentation: Mention `appdirs` (by e-dschungel)

### Fixed
- SMTP: Fix handling of missing `user` field (by e-dschungel)
- Manpage: Fix documentation of XDG environment variables (by Jelle van der Waa)
- Unit tests: Fix imports for out-of-source-tree tests (by Maxime Werlen)


## [2.7] -- 2017-11-08

### Added
- Filtering: `style` (by gvandenbroucke), `tag` (by cmichi)
- New reporter: Telegram support (by gvandenbroucke)
- Paths: Add `XDG_CONFIG_DIR` support (by Jelle van der Waa)

### Changed
- ElementsByAttribute: look for matching tag in handle_endtag (by Gaetan Leurent)
- HTTP: Option to avoid 304 responses, `Content-Type` header (by Vinicius Massuchetto)
- html2text: Configuration options (by Vinicius Massuchetto)

### Fixed
- Issue #127: Fix error reporting
- E-Mail: Fix encodings (by Seokjin Han), Allow `user` parameter for SMTP (by Jay Sitter)


## [2.6] -- 2016-12-04

### Added
- New filters: `sha1sum`, `hexdump`, `element-by-class`
- New reporters: pushbullet (by R0nd); mailgun (by lechuckcaptain)

### Changed
- Improved filters: `BeautifulSoup` support for `html2txt` (by lechuckcaptain)
- Improved handlers: HTTP Proxy (by lechuckcaptain); support for `file://` URIs
- CI Integration: Build configuration for Travis CI (by lechuckcaptain)
- Consistency: Feature list is now sorted by name

### Fixed
- Issue #108: Fix creation of example files on first startup
- Issue #118: Fix match filters for missing keys
- Small fixes by: Jakub Wilk, Marc Urben, Adam Dobrawy and Louis Sautier


Older ChangeLog entries can be found in the
[old ChangeLog file](https://github.com/thp/urlwatch/blob/2.12/ChangeLog),
or with `git show 2.12:ChangeLog` on the command line.
