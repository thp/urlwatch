import importlib

from docutils.nodes import literal_block
from docutils.parsers.rst import Directive, directives


def patch_subclasses(klass):
    """ Recursively patch urlwatch classes to behave like standard python classes. """
    klass.__subclasses__ = type.__subclasses__.__get__(klass)

    for kls in klass.__subclasses__():
        patch_subclasses(kls)


def build_tree(klass, level):
    """ Recurse into klass to build tree. """
    for i, kls in enumerate(klass.__subclasses__()):
        branch = '└───' if i + 1 == len(klass.__subclasses__()) else '├───'
        indent = '│   ' * (level - 1)
        yield ('' if level == 0 else indent + branch) + kls.__kind__

        yield from build_tree(kls, level + 1)


class InheritanceAsciiTree(Directive):
    required_arguments = 1

    def run(self):
        rootparts = self.arguments.pop().split('.')
        rootname = rootparts.pop()
        rootmodulename = '.'.join(rootparts)

        rootmodule = importlib.import_module(rootmodulename)
        root = getattr(rootmodule, rootname)

        patch_subclasses(root)

        tree = (element for element in build_tree(root, 0))
        treestring = '\n'.join(tree)
        return [literal_block(treestring, treestring)]


def setup(app):
    app.add_directive('inheritance-ascii-tree', InheritanceAsciiTree)
