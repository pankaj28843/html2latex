# Standard Library
import os

# Third Party Stuff
from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand
from pip.req import parse_requirements


# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements(os.path.join(
    os.path.dirname(__file__),
    'requirements.txt',
))

REQUIREMENTS = [str(ir.req) for ir in install_reqs]


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


class NoseTestCommand(TestCommand):
    # Inspired by the example at https://pytest.org/latest/goodpractises.html

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # Run nose ensuring that argv simulates running nosetests directly
        import nose
        nose.run_exit(argv=['nosetests'])

setup(
    name="html2latex",
    version="0.0.2",
    author="Pankaj Singh",
    author_email="pankaj@policyinnovations.in",
    description=("Convert HTML to latex."),
    license = "BSD",
    keywords = "html, latex",
    url = "http://packages.python.org/pypi/html2latex",
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['html2latex'],
    install_requires=REQUIREMENTS,
    cmdclass={'test': NoseTestCommand},
    test_suite = "nose.collector",
    include_package_data=True,
    zip_safe=False,
)
