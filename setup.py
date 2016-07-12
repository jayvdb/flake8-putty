#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Flake8 putty setup module."""
from __future__ import absolute_import, unicode_literals, with_statement

import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand  # flake8: disable=H306,N812


class PyTest(TestCommand):

    """Test harness."""

    user_options = []

    def initialize_options(self):
        """Initialise options hook."""
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def run_tests(self):
        """Run tests hook."""
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


def get_version(fname='flake8_putty/__init__.py'):
    """Get __version__ from package __init__."""
    with open(fname) as f:
        for line in f:
            if line.startswith('__version__'):
                return eval(line.split('=')[-1])


def get_long_description():
    """Load README.rst."""
    descr = []
    for fname in ('README.rst',):
        with open(fname) as f:
            descr.append(f.read())
    return '\n\n'.join(descr)


tests_require = ['pytest']
if sys.version_info < (3, 3):
    tests_require.append('mock')
if sys.version_info < (2, 7):
    tests_require.append('unittest2')

setup(
    name='flake8-putty',
    version=get_version(),
    description='Apply a bit of putty to flake8.',
    long_description=get_long_description(),
    keywords='flake8 pep8 putty',
    author='John Vandenberg',
    author_email='jayvdb@gmail.com',
    url='https://github.com/jayvdb/flake8-putty',
    install_requires=[
        # extensions were introduced in 2.0
        # flake8 v3 internals are very different
        'flake8>=2,<3',
        'packaging>=16.0',
    ],
    license='MIT',
    packages=[str('flake8_putty')],
    zip_safe=False,
    entry_points={
        'flake8.extension': [
            'flake8_putty = flake8_putty:PuttyExtension',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Quality Assurance',
    ],
    tests_require=tests_require,
    cmdclass={'test': PyTest},
)
