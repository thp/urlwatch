import datetime

import pytest

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
    report.config["report"]["markdown"]["footer"] = False
    job_state = _DummyJobState(diff="line1\nline2\nline3")
    reporter = MarkdownReporter(report, report.config["report"]["markdown"], [job_state], datetime.timedelta(), 1)

    output = list(reporter.submit(max_length=None))

    assert any("```diff" in line for line in output)
    assert "[...]" not in "\n".join(output)


def test_markdown_submit_without_max_length_preserves_trailing_separator():
    report = _DummyReport()
    report.config["report"]["markdown"]["details"] = False
    report.config["report"]["markdown"]["footer"] = False
    job_state = _DummyJobState(old_data=None)
    reporter = MarkdownReporter(report, report.config["report"]["markdown"], [job_state], datetime.timedelta(), 1)

    output = list(reporter.submit(max_length=None))

    assert output == ["1. CHANGED: dummy", ""]


def test_markdown_submit_with_trimming_returns_notice():
    report = _DummyReport()
    job_state = _DummyJobState(diff="line1\nline2\nline3")
    reporter = MarkdownReporter(report, report.config["report"]["markdown"], [job_state], datetime.timedelta(), 1)

    output = list(reporter.submit(max_length=80))

    assert "[...]" in output


def test_markdown_submit_short_marker_preserves_content():
    report = _DummyReport()
    report.config["report"]["markdown"]["footer"] = False
    job_state = _DummyJobState(diff="line1\nline2\nline3")
    reporter = MarkdownReporter(report, report.config["report"]["markdown"], [job_state], datetime.timedelta(), 1)

    output = list(reporter.submit(max_length=58))

    assert "1. CHANGED: dummy" in output
    assert "### CHANGED: dummy" in output
    assert "[...]" in output
    assert len("\n".join(output)) <= 58


@pytest.mark.parametrize("footer", [False, True])
def test_markdown_submit_does_not_exceed_max_length(footer):
    report = _DummyReport()
    report.config["report"]["markdown"]["footer"] = footer
    job_state = _DummyJobState(diff="line1\nline2\nline3")
    reporter = MarkdownReporter(report, report.config["report"]["markdown"], [job_state], datetime.timedelta(), 1)

    for max_length in range(201):
        output = list(reporter.submit(max_length=max_length))

        assert len("\n".join(output)) <= max_length


def test_markdown_submit_keeps_trimmed_detail_body():
    report = _DummyReport()
    report.config["report"]["markdown"]["footer"] = False
    job_state = _DummyJobState(diff="x" * 500)
    reporter = MarkdownReporter(report, report.config["report"]["markdown"], [job_state], datetime.timedelta(), 1)

    max_length = 200
    output = list(reporter.submit(max_length=max_length))

    assert any("*diff trimmed*" in line for line in output)
    assert len("\n".join(output)) <= max_length


def test_markdown_submit_keeps_short_detail_after_oversized_detail():
    report = _DummyReport()
    report.config["report"]["markdown"]["footer"] = False
    job_states = [_DummyJobState(diff="x" * 500), _DummyJobState(diff="ok")]
    reporter = MarkdownReporter(report, report.config["report"]["markdown"], job_states, datetime.timedelta(), 2)

    max_length = 153
    output = list(reporter.submit(max_length=max_length))

    assert "```diff\nok\n```" in output
    assert len("\n".join(output)) <= max_length


def test_markdown_submit_does_not_render_oversized_body_without_limit(monkeypatch):
    calls = []
    original = MarkdownReporter._format_details_body

    def track_call(body, max_length):
        result = original(body, max_length)
        calls.append((max_length, len(result[1])))
        return result

    monkeypatch.setattr(MarkdownReporter, "_format_details_body", staticmethod(track_call))

    report = _DummyReport()
    report.config["report"]["markdown"]["footer"] = False
    job_state = _DummyJobState(diff="line\n" * 20_000)
    reporter = MarkdownReporter(report, report.config["report"]["markdown"], [job_state], datetime.timedelta(), 1)

    max_length = 16 * 1024
    output = list(reporter.submit(max_length=max_length))

    assert calls
    assert all(call_max_length is not None for call_max_length, _ in calls)
    assert all(rendered_length <= max_length for _, rendered_length in calls)
    assert "[...]" in output
    assert len("\n".join(output)) <= max_length


def test_markdown_format_details_body_does_not_exceed_small_limits():
    for max_length in range(28):
        trimmed, body = MarkdownReporter._format_details_body("x" * 100_000, max_length)

        assert trimmed
        assert len(body) <= max_length


def test_markdown_join_up_to_length_stops_after_limit():
    def lines():
        yield "abc"
        yield "def"
        raise AssertionError("Consumed lines beyond the requested length")

    assert MarkdownReporter._join_up_to_length(lines(), 5) == "abc\nd"


def test_markdown_submit_with_tiny_max_length_preserves_content_or_marker():
    report = _DummyReport()
    job_state = _DummyJobState(diff="line1\nline2\nline3")
    reporter = MarkdownReporter(report, report.config["report"]["markdown"], [job_state], datetime.timedelta(), 1)

    assert list(reporter.submit(max_length=0)) == []
    assert list(reporter.submit(max_length=4)) == ["1. C"]
    assert list(reporter.submit(max_length=5)) == ["[...]"]


def test_markdown_submit_trims_with_footer():
    report = _DummyReport()
    job_state = _DummyJobState(diff=("line\n" * 200))
    reporter = MarkdownReporter(report, report.config["report"]["markdown"], [job_state], datetime.timedelta(), 1)

    max_length = None
    output = []
    for length in range(80, 200):
        output = list(reporter.submit(max_length=length))
        if "--- " in output and "[...]" in output:
            max_length = length
            break

    assert max_length is not None
    rendered_output = "\n".join(output)
    assert "[...]\n\n--- " in rendered_output
    assert len(rendered_output) <= max_length


def test_markdown_submit_does_not_trim_when_length_exact():
    report = _DummyReport()
    report.config["report"]["markdown"]["details"] = False
    report.config["report"]["markdown"]["footer"] = False
    job_state = _DummyJobState(old_data=None)
    reporter = MarkdownReporter(report, report.config["report"]["markdown"], [job_state], datetime.timedelta(), 1)

    max_length = len("1. CHANGED: dummy")
    output = list(reporter.submit(max_length=max_length))

    assert "\n".join(output) == "1. CHANGED: dummy"
    assert "[...]" not in "\n".join(output)


def test_markdown_submit_does_not_trim_details_when_length_exact():
    report = _DummyReport()
    report.config["report"]["markdown"]["footer"] = False
    job_state = _DummyJobState(diff="line1\nline2")
    reporter = MarkdownReporter(report, report.config["report"]["markdown"], [job_state], datetime.timedelta(), 1)

    full_output = list(reporter.submit(max_length=16 * 1024))
    exact_output = list(reporter.submit(max_length=len("\n".join(full_output))))

    assert exact_output == full_output
    assert "[...]" not in "\n".join(exact_output)


def test_markdown_submit_trims_when_one_character_over_limit():
    report = _DummyReport()
    report.config["report"]["markdown"]["details"] = False
    report.config["report"]["markdown"]["footer"] = False
    job_state = _DummyJobState(old_data=None)
    reporter = MarkdownReporter(report, report.config["report"]["markdown"], [job_state], datetime.timedelta(), 1)

    max_length = len("1. CHANGED: dummy") - 1
    output = list(reporter.submit(max_length=max_length))

    expected = "1. CHANGED: dummy"[:max_length - len("[...]")] + "[...]"
    assert output == [expected]
    assert len("\n".join(output)) <= max_length
