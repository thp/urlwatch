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

    output = list(reporter.submit(max_length=10))

    assert any("Parts of the report were omitted" in line for line in output)
