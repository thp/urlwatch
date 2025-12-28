import datetime

from urlwatch.reporters import MarkdownReporter


class _DummyJob:
    def pretty_name(self):
        return "dummy"

    def get_location(self):
        return "dummy"


class _DummyJobState:
    def __init__(self, verb="changed", old_data="old", new_data="new", diff="diff"):
        self.job = _DummyJob()
        self.verb = verb
        self.old_data = old_data
        self.new_data = new_data
        self._diff = diff
        self.traceback = "traceback"

    def get_diff(self):
        return self._diff


class _DummyReport:
    def __init__(self):
        self.config = {
            "report": {
                "markdown": {
                    "details": True,
                    "footer": True,
                    "minimal": False,
                    "separate": False,
                }
            }
        }

    def get_filtered_job_states(self, job_states):
        return job_states


def test_markdown_submit_without_max_length_does_not_crash():
    report = _DummyReport()
    reporter = MarkdownReporter(report, report.config["report"]["markdown"], [], datetime.timedelta())

    output = list(reporter.submit(max_length=None))

    assert output == []


def test_markdown_submit_with_trimming_returns_notice():
    report = _DummyReport()
    job_state = _DummyJobState(diff="line1\nline2\nline3")
    reporter = MarkdownReporter(report, report.config["report"]["markdown"], [job_state], datetime.timedelta())

    output = list(reporter.submit(max_length=80))

    assert any("Parts of the report were omitted" in line for line in output)


def test_markdown_submit_uses_fallback_marker_when_notice_too_long():
    report = _DummyReport()
    report.config["report"]["markdown"]["footer"] = False
    job_state = _DummyJobState(diff="line1\nline2\nline3")
    reporter = MarkdownReporter(report, report.config["report"]["markdown"], [job_state], datetime.timedelta())

    output = list(reporter.submit(max_length=30))

    assert any("[...]" in line for line in output)
    assert not any("Parts of the report were omitted" in line for line in output)


def test_markdown_submit_with_tiny_max_length_does_not_exceed_limit():
    report = _DummyReport()
    job_state = _DummyJobState(diff="line1\nline2\nline3")
    reporter = MarkdownReporter(report, report.config["report"]["markdown"], [job_state], datetime.timedelta())

    max_length = 5
    output = list(reporter.submit(max_length=max_length))

    total_length = sum(len(line) + 1 for line in output) - 1 if output else 0
    assert total_length <= max_length


def test_markdown_submit_with_zero_max_length_is_empty():
    report = _DummyReport()
    job_state = _DummyJobState(diff="line1\nline2\nline3")
    reporter = MarkdownReporter(report, report.config["report"]["markdown"], [job_state], datetime.timedelta())

    output = list(reporter.submit(max_length=0))

    assert output == []


def test_markdown_submit_trims_with_footer():
    report = _DummyReport()
    job_state = _DummyJobState(diff=("line\n" * 200))
    reporter = MarkdownReporter(report, report.config["report"]["markdown"], [job_state], datetime.timedelta())

    max_length = None
    output = []
    for length in range(80, 200):
        output = list(reporter.submit(max_length=length))
        if (any("urlwatch" in line for line in output)
                and any("Parts of the report were omitted" in line for line in output)):
            max_length = length
            break

    assert max_length is not None


def test_markdown_submit_does_not_trim_when_length_exact():
    report = _DummyReport()
    report.config["report"]["markdown"]["details"] = False
    report.config["report"]["markdown"]["footer"] = False
    job_state = _DummyJobState(old_data=None)
    reporter = MarkdownReporter(report, report.config["report"]["markdown"], [job_state], datetime.timedelta())

    max_length = len("1. CHANGED: dummy")
    output = list(reporter.submit(max_length=max_length))

    assert not any("Parts of the report were omitted" in line for line in output)
