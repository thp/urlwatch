from urlwatch.handler import JobState
from urlwatch.jobs import ShellJob
from nose.tools import eq_, raises

job_state = JobState('', ShellJob(command=''))
job_state.timestamp = 0

def test_generate_diff_normal():
    '''Base case'''
    job_state.old_data = 'a\n'
    job_state.new_data = 'b\n'
    job_state.job.comparison_filter = None
    expected = ['@@ -1 +1 @@',
                '-a',
                '+b']
    diff = job_state._generate_diff()
    eq_(diff.splitlines()[2:], expected)

@raises(ValueError)
def test_generate_diff_comparison_filter_unknown():
    '''use of unknown comparison_filter (ValueError)'''
    job_state.job.comparison_filter = 'blabla'
    diff = job_state._generate_diff()

def test_generate_diff_comparison_filter_additions():
    '''changed line with "additions" comparison_filter'''
    job_state.old_data = 'a\n'
    job_state.new_data = 'b\n'
    job_state.job.comparison_filter = 'additions'
    expected = ['-**Comparison type: Additions only**',
                '@@ -1 +1 @@',
                '+b']
    diff = job_state._generate_diff()
    eq_(diff.splitlines()[2:], expected)

def test_generate_diff_comparison_filter_deletions():
    '''changed line with "deletions" comparison_filter'''
    job_state.old_data = 'a\n'
    job_state.new_data = 'b\n'
    job_state.job.comparison_filter = 'deletions'
    expected = ['+**Comparison type: Deletions only**',
                '@@ -1 +1 @@',
                '-a']
    diff = job_state._generate_diff()
    eq_(diff.splitlines()[2:], expected)

def test_generate_diff_comparison_filter_additions_75pct_deleted():
    '''"additions" comparison_filter with 75% or more of original content deleted'''
    job_state.old_data = 'a\nb\nc\nd\n'
    job_state.new_data = 'd\n'
    job_state.job.comparison_filter = 'additions'
    expected = ['-**Comparison type: Additions only**',
                '-**Deletions are being shown as 75% or more of the content has been deleted**',
                '@@ -1,3 +0,0 @@',
                '-a',
                '-b',
                '-c']
    diff = job_state._generate_diff()
    eq_(diff.splitlines()[2:], expected)

def test_generate_diff_comparison_filter_additions_only_deletions():
    '''"additions" comparison_filter and lines were only deleted'''
    job_state.old_data = 'a\nb\nc\nd\n'
    job_state.new_data = 'a\nb\nc\n'
    job_state.job.comparison_filter = 'additions'
    expected = False
    eq_(job_state._generate_diff(), expected)

def test_generate_diff_comparison_filter_deletions_only_additions():
    '''"deletions" comparison_filter and lines were only added'''
    job_state.old_data = 'a\n'
    job_state.new_data = 'a\nb\n'
    job_state.job.comparison_filter = 'deletions'
    expected = False
    eq_(job_state._generate_diff(), expected)