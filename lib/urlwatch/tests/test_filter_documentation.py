import docutils.nodes
import docutils.parsers.rst
import docutils.utils
import docutils.frontend

import os
import yaml
import pytest


from urlwatch.filters import FilterBase

root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
here = os.path.dirname(__file__)


# https://stackoverflow.com/a/48719723/1047040
def parse_rst(text):
    parser = docutils.parsers.rst.Parser()
    components = (docutils.parsers.rst.Parser,)
    settings = docutils.frontend.OptionParser(components=components).get_default_values()
    document = docutils.utils.new_document('<rst-doc>', settings=settings)
    parser.parse(text, document)
    return document


# https://stackoverflow.com/a/48719723/1047040
class YAMLCodeBlockVisitor(docutils.nodes.NodeVisitor):
    def __init__(self, doc):
        super().__init__(doc)
        self.jobs = []

    def visit_literal_block(self, node):
        if 'yaml' in node.attributes['classes']:
            self.jobs.append(yaml.safe_load(node.astext()))

    def unknown_visit(self, node: docutils.nodes.Node) -> None:
        ...


def load_filter_testdata():
    doc = parse_rst(open(os.path.join(root, 'docs/source/filters.rst')).read())
    visitor = YAMLCodeBlockVisitor(doc)
    doc.walk(visitor)

    jobs = {job['url']: job for job in visitor.jobs}

    # Make sure all URLs are unique
    assert len(jobs) == len(visitor.jobs)

    return jobs


FILTER_DOC_URLS = load_filter_testdata()


@pytest.mark.parametrize('url, job', FILTER_DOC_URLS.items())
def test_url(url, job):
    testdata = yaml.safe_load(open(os.path.join(here, 'data/filter_documentation_testdata.yaml')).read())
    d = testdata[url]
    if 'filename' in d:
        input_data = open(os.path.join(here, 'data', d['filename']), 'rb').read()
    else:
        input_data = d['input']

    for filter_kind, subfilter in FilterBase.normalize_filter_list(job['filter']):
        filtercls = FilterBase.__subclasses__[filter_kind]
        input_data = filtercls(None, None).filter(input_data, subfilter)
        # TODO: FilterBase.process(cls, filter_kind, subfilter, state, data):

    output_data = d['output']
    assert input_data == output_data
