# -*- coding: utf-8 -*-
"""Test config parser."""
from __future__ import unicode_literals

import os.path

from unittest import TestCase

try:
    from unittest import mock
except ImportError:
    import mock  # Python 3.2 and lower

from flake8 import engine

from flake8_putty.config import IS_WINDOWS

pep8 = engine.pep8

# Ignore unrelated flake8 plugins
IGNORE_LIST = ('FI', 'D')
_IGNORE_OPTION = '--ignore={0}'.format(','.join(IGNORE_LIST))

# Use a real filename `tests/__init__.py` to avoid
# https://github.com/ar4s/flake8_tuple/issues/8


class IntegrationTestBase(TestCase):

    """Integration test framework."""

    @classmethod
    def setUpClass(cls):
        flake8_ext_data = engine._register_extensions()
        flake8_ext_list = flake8_ext_data[0]
        assert flake8_ext_list
        flake8_ext_names = [item[0] for item in flake8_ext_list]
        assert 'flake8-putty' in flake8_ext_names

    def check_files(self, fake_stdin=None, arglist=None, explicit_stdin=True,
                    filename=None, count=0):
        """Call check_files and verify error count."""
        arglist = arglist or []

        ignore_used = any(x.startswith('--putty-ignore') for x in arglist)
        if not ignore_used:
            arglist.append('--putty-ignore=')

        if '--putty-auto-ignore' not in arglist:
            arglist.append('--putty-no-auto-ignore')

        if explicit_stdin:
            arglist.append('-')

        argv = ['flake8', _IGNORE_OPTION] + arglist

        with mock.patch("sys.argv", argv):
            style_guide = engine.get_style_guide(parse_argv=True)

        with mock.patch(pep8.__name__ + '.stdin_get_value', fake_stdin):
            if filename:
                results = style_guide.input_file(
                    filename,
                    lines=pep8.stdin_get_value().splitlines(True),
                )
                total_errors = results
            else:
                report = style_guide.check_files()
                total_errors = report.total_errors
        self.assertEqual(total_errors, count)
        return style_guide, total_errors


class TestFlake8(IntegrationTestBase):

    """Integration tests for flake8 itself."""

    def test_stdin(self):
        def fake_stdin():
            return "notathing\n"
        self.check_files(fake_stdin, count=1)

    def test_filename(self):
        def fake_stdin():
            return "notathing\n"
        self.check_files(
            fake_stdin,
            filename='tests/__init__.py',
            count=1,
        )

    def test_filename_explicit_relative(self):
        def fake_stdin():
            return "notathing\n"
        self.check_files(
            fake_stdin,
            filename='./tests/__init__.py',
            count=1,
        )

    def test_filename_absolute(self):
        def fake_stdin():
            return "notathing\n"
        self.check_files(
            fake_stdin,
            filename=os.path.abspath('tests/__init__.py'),
            count=1,
        )


class TestIgnoreFile(IntegrationTestBase):

    """Integration tests for ignoring with filenames."""

    def test_ignore_filename(self):
        def fake_stdin():
            return "notathing\n"
        self.check_files(
            fake_stdin,
            arglist=['--putty-ignore=tests/__init__.py : +F821'],
            filename='tests/__init__.py',
        )

    def test_ignore_filename_explicit_relative(self):
        # FIXME(#9): explicit relative should match in both below, i.e count=0,
        # on all platforms.
        def fake_stdin():
            return "notathing\n"
        self.check_files(
            fake_stdin,
            arglist=['--putty-ignore=./tests/__init__.py : +F821'],
            filename='tests/__init__.py',
            count=1,
        )

        self.check_files(
            fake_stdin,
            arglist=['--putty-ignore=./tests/__init__.py : +F821'],
            filename='./tests/__init__.py',
            count=0 if IS_WINDOWS else 1,
        )

    def test_ignore_filename_absolute_not_matched(self):
        """Verify absolute filenames are not ignorable."""
        def fake_stdin():
            return "notathing\n"
        self.check_files(
            fake_stdin,
            arglist=['--putty-ignore=tests/__init__.py : +F821'],
            filename=os.path.abspath('tests/__init__.py'),
            count=1,
        )


class TestIgnoreTrailingNewLine(IntegrationTestBase):

    r"""Integration tests for matching against trailing \n in line."""

    # The physical line sent to match routines includes a trailing '\n'
    # which should not cause a second input line for the regex.
    # test_line_end_regex and test_blank_line_regex confirms that
    # the most likely problems do not exist.

    # FIXME(very low importance): The tests test_new_line_regex and
    # test_multiline_blank_line_regex shows that the \n is causing matches
    # inappropriately, as it hides the error.
    # As these are the only strange results with the current physical line,
    # it is easier to reject these regex rather than change the match process.
    # Note that multi-line regex mode is not supported for physical lines,
    # but it doesnt appear to expose any additional real world bugs.

    def test_line_end_regex(self):
        def fake_stdin():
            return "notathing\n"
        self.check_files(
            fake_stdin,
            arglist=['--putty-ignore=/notathing$/ : +F821'],
            count=0,
        )

    def test_blank_line_regex(self):
        def fake_stdin():
            return "notathing\n"
        self.check_files(
            fake_stdin,
            arglist=['--putty-ignore=/^$/ : +F821'],
            count=1,
        )

    def test_new_line_regex(self):
        def fake_stdin():
            return "notathing\n"
        self.check_files(
            fake_stdin,
            arglist=['--putty-ignore=/\\n/ : +F821'],
            count=0,
        )

    def test_multiline_blank_line_regex(self):
        def fake_stdin():
            return "notathing\n"
        self.check_files(
            fake_stdin,
            arglist=['--putty-ignore=/(?m)^$/ : +F821'],
            count=0,
        )

    def test_multiline_line_end_regex(self):
        # End of line is still matched correctly.
        def fake_stdin():
            return "notathing\n"
        self.check_files(
            fake_stdin,
            arglist=['--putty-ignore=/(?m)^notathing$/ : +F821'],
            count=0,
        )


class TestIgnoreRegex(IntegrationTestBase):

    """Integration tests for ignoring with regex."""

    def test_ignore_regex(self):
        def fake_stdin():
            return "notathing\n"
        self.check_files(
            fake_stdin,
            arglist=['--putty-ignore=/notathing/ : +F821'],
        )

    def test_ignore_multi(self):
        def fake_stdin():
            return "notathing # foo\n"
        self.check_files(
            fake_stdin,
            arglist=['--putty-ignore=/notathing/ : +E261,F821'],
        )

    def test_auto_ignore(self):
        def fake_stdin():
            return "notathing  # flake8: disable=F821\n"
        self.check_files(
            fake_stdin,
            arglist=['--putty-auto-ignore'],
        )

    def test_auto_ignore_disabled(self):
        def fake_stdin():
            return "notathing  # flake8: disable=F821\n"
        self.check_files(
            fake_stdin,
            arglist=['--putty-no-auto-ignore'],
            count=1,
        )

    def test_auto_ignore_missing_code(self):
        def fake_stdin():
            return "notathing  # flake8: disable=\n"
        self.check_files(
            fake_stdin,
            arglist=['--putty-auto-ignore'], count=1,
        )

    def test_auto_ignore_multi_regex(self):
        def fake_stdin():
            return "notathing # flake8: disable=F821\n"
        self.check_files(
            fake_stdin,
            arglist=[
                '--putty-auto-ignore',
                '--putty-ignore=/notathing/ : +E261',
            ],
        )

    def test_auto_ignore_multi_filename(self):
        def fake_stdin():
            return "notathing # flake8: disable=F821\n"
        self.check_files(
            fake_stdin,
            arglist=[
                '--putty-auto-ignore',
                '--putty-ignore=tests/__init__.py : +E261',
            ],
            filename='tests/__init__.py',
        )
