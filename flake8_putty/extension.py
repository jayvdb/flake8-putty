# -*- coding: utf-8 -*-
"""Flake8 putty extension."""
from __future__ import absolute_import, unicode_literals

import functools
import sys

from flake8_putty.config import Parser, RegexRule, RegexSelector


# Copied from pep.StyleGuide.ignore_code
def ignore_code(options, code):
    """
    Check if the error code should be ignored.

    If 'options.select' contains a prefix of the error code,
    return False.  Else, if 'options.ignore' contains a prefix of
    the error code, return True.
    """
    if len(code) < 4 and any(s.startswith(code)
                             for s in options.select):
        return False
    return (code.startswith(options.ignore) and
            not code.startswith(options.select))


def get_reporter_state():
    """Get pep8 reporter state from stack."""
    # Stack
    # 1. get_reporter_state (i.e. this function)
    # 2. putty_ignore_code
    # 3. QueueReport.error or pep8.StandardReport.error for flake8 -j 1
    # 4. pep8.Checker.check_ast or check_physical or check_logical
    #    locals contains `tree` (ast) for check_ast
    frame = sys._getframe(3)
    reporter = frame.f_locals['self']
    line_number = frame.f_locals['line_number']
    offset = frame.f_locals['offset']
    text = frame.f_locals['text']
    check = frame.f_locals['check']
    return reporter, line_number, offset, text, check


def putty_ignore_code(options, code):
    """Hook for pep8 'ignore_code'."""
    reporter, line_number, offset, text, check = get_reporter_state()
    try:
        line = reporter.lines[line_number - 1]
    except IndexError:
        line = ''

    options.ignore = options._orig_ignore
    options.select = options._orig_select

    for rule in options.putty_ignore:
        if rule.match(reporter.filename, line, list(reporter.counters) + [code]):
            if rule._append_codes:
                options.ignore = options.ignore + rule.codes
            else:
                options.ignore = rule.codes

    for rule in options.putty_select:
        if rule.match(reporter.filename, line, list(reporter.counters) + [code]):
            if rule._append_codes:
                options.select = options.select + rule.codes
            else:
                options.select = rule.codes

    return ignore_code(options, code)


class AutoLineDisableSelector(RegexSelector):

    """Auto-selector."""

    _text = '#.*flake8: disable=(?P<codes>[A-Z0-9, ]*)'

    def __repr__(self):
        return 'AutoLineDisableSelector()'


class AutoLineDisableRule(RegexRule):

    """Rule matching # flake8: disable=x,y ."""

    def __init__(self):
        """Constructor."""
        super(AutoLineDisableRule, self).__init__(
            [AutoLineDisableSelector()],
            ['(?P<codes>)'],
        )
        self._append_codes = True

    def __repr__(self):
        return 'AutoLineDisableRule()'


class PuttyExtension(object):

    """Flake8 extension for customising error reporting."""

    name = 'flake8-putty'
    version = None  # set in package __init__

    def __init__(self):
        """Constructor."""
        # Must exist for flake8 inspection of the extension

    @classmethod
    def add_options(cls, parser):
        """Add options for command line and config file."""
        parser.add_option(
            '--putty-select', metavar='errors', default='',
            help='putty select list',
        )
        parser.add_option(
            '--putty-ignore', metavar='errors', default='',
            help='putty ignore list',
        )
        parser.add_option(
            '--putty-no-auto-ignore', action='store_false',
            dest='putty_auto_ignore', default=False,
            help=(' (default) do not auto ignore lines matching '
                  '# flake8: disable=<code>,<code>'),
        )
        parser.add_option(
            '--putty-auto-ignore', action='store_true',
            dest='putty_auto_ignore', default=False,
            help=('auto ignore lines matching '
                  '# flake8: disable=<code>,<code>'),
        )
        parser.config_options.append('putty-select')
        parser.config_options.append('putty-ignore')
        parser.config_options.append('putty-auto-ignore')

    @classmethod
    def parse_options(cls, options):
        """Parse options and activate `ignore_code` handler."""
        if (not options.putty_select and not options.putty_ignore and
                not options.putty_auto_ignore):
            return

        options._orig_select = options.select
        options._orig_ignore = options.ignore

        options.putty_select = Parser(options.putty_select)._rules
        options.putty_ignore = Parser(options.putty_ignore)._rules

        if options.putty_auto_ignore:
            options.putty_ignore.append(AutoLineDisableRule())

        options.ignore_code = functools.partial(
            putty_ignore_code,
            options,
        )

        options.report._ignore_code = options.ignore_code
