import pycodestyle
import os
import site


def test_pep8_conformance():
    """Test that we conform to PEP-8."""
    style = pycodestyle.StyleGuide(ignore=['E501', 'E402', 'W503', 'E241'])

    site_packages = site.getsitepackages()

    def py_files():
        for dir, dirs, files in os.walk(os.path.abspath('.')):
            if dir in site_packages:
                dirs.clear()  # os.walk lets us modify the dirs list to prune the walk
                files.clear()  # we also don't want to process files in the root of this excluded dir
            for file in files:
                if file.endswith('.py'):
                    yield os.path.join(dir, file)

    result = style.check_files(py_files())
    assert result.total_errors == 0, "Found #{0} code style errors".format(result.total_errors)
