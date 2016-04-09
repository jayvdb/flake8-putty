# -*- coding: utf-8 -*-
"""Test config parser."""
from __future__ import unicode_literals

from unittest import TestCase

try:
    from unittest import mock
except ImportError:
    import mock  # Python 3.2 and lower

from flake8 import engine

import pep8

# Ignore unrelated flake8 plugins
IGNORE_LIST = ('FI', 'D')
_IGNORE_OPTION = '--ignore={0}'.format(','.join(IGNORE_LIST))


class TestIntegration(TestCase):

    """Integration style tests to exercise different command line options."""

    def check_files(self, arglist=None, explicit_stdin=True, filename=None,
                    count=0):
        """Call check_files and verify error count."""
        arglist = arglist or []
        if explicit_stdin:
            arglist.append('-')

        argv = ['flake8', _IGNORE_OPTION] + arglist
        with mock.patch("sys.argv", argv):
            style_guide = engine.get_style_guide(parse_argv=True)
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

    def test_stdin(self):
        def fake_stdin():
            return "notathing\n"
        with mock.patch("pep8.stdin_get_value", fake_stdin):
            guide, report = self.check_files(count=1)

    def test_ignore(self):
        def fake_stdin():
            return "notathing\n"
        with mock.patch("pep8.stdin_get_value", fake_stdin):
            guide, report = self.check_files(
                arglist=['--putty-ignore=/notathing/ : +F821'],
            )

    def test_ignore_multi(self):
        def fake_stdin():
            return "notathing # foo\n"
        with mock.patch("pep8.stdin_get_value", fake_stdin):
            guide, report = self.check_files(
                arglist=['--putty-ignore=/notathing/ : +E261,F821'],
            )

    def test_auto_ignore(self):
        def fake_stdin():
            return "notathing  # flake8: disable=F821\n"
        with mock.patch("pep8.stdin_get_value", fake_stdin):
            guide, report = self.check_files(
                arglist=['--putty-auto-ignore'],
            )

    def test_auto_ignore_missing_code(self):
        def fake_stdin():
            return "notathing  # flake8: disable=\n"
        with mock.patch("pep8.stdin_get_value", fake_stdin):
            guide, report = self.check_files(
                arglist=['--putty-auto-ignore'], count=1,
            )

    def test_auto_ignore_line_continuation_ast(self):
        def fake_stdin():
            return (
                "notathing and \\\n"
                "    1 and \\\n"
                "    2  # flake8: disable=F821\n"
            )
        with mock.patch("pep8.stdin_get_value", fake_stdin):
            guide, report = self.check_files(
                arglist=['--putty-auto-ignore'],
            )

    def test_auto_ignore_line_continuation_physical(self):
        def fake_stdin():
            return "def foo():\n\t1 and \\\n\t\t2  # flake8: disable=W191\n"

        with mock.patch("pep8.stdin_get_value", fake_stdin):
            guide, report = self.check_files(
                arglist=['--putty-auto-ignore'],
            )

    # MUSTDO: test global regex ; i.e. two lines with # flake8:...

    def test_auto_ignore_line_continuation_logical(self):
        def fake_stdin():
            return "y = 1 , \\\n    2  # flake8: disable=E203\n"

        with mock.patch("pep8.stdin_get_value", fake_stdin):
            guide, report = self.check_files(
                arglist=['--putty-auto-ignore'],
            )

    def test_auto_ignore_multi_regex(self):
        def fake_stdin():
            return "notathing # flake8: disable=F821\n"
        with mock.patch("pep8.stdin_get_value", fake_stdin):
            guide, report = self.check_files(
                arglist=['--putty-auto-ignore',
                         '--putty-ignore=/notathing/ : +E261'],
            )

    def test_auto_ignore_multi_filename(self):
        # Use a real filename `tests/__init__.py` to avoid
        # https://github.com/ar4s/flake8_tuple/issues/8
        def fake_stdin():
            return "notathing # flake8: disable=F821\n"
        with mock.patch("pep8.stdin_get_value", fake_stdin):
            guide, report = self.check_files(
                arglist=['--putty-auto-ignore',
                         '--putty-ignore=tests/__init__.py : +E261'],
                filename='tests/__init__.py',
            )
