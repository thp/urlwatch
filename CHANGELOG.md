# Changelog

All notable changes to this project will be documented in this file.

The format mostly follows [Keep a Changelog](http://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Fixed
- Fix `--test-filter` when the specified job is not found

### Changed
- Nicer formatting of `--features` for jobs with no docstring or many keys


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
- CLI: Allow multiple occurences of 'filter' when adding jobs (PR#278)

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
