# -*- coding: utf-8 -*-
"""Flake8 putty extension."""
from __future__ import absolute_import, unicode_literals

import functools
import sys

from flake8_putty.config import Parser


# Copied from pep.StyleGuide.ignore_code
def ignore_code(options, code):
    """Check if the error code should be ignored.

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
    line = reporter.lines[line_number - 1]

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


class PuttyExtension(object):

    """Flake8 extension for customising error reporting."""

    name = 'flake8-putty'
    version = None  # set in package __init__

    def __init__(self):
        """Constructor."""
        # Must exist for flake8 inspection of the extension
        pass

    @classmethod
    def add_options(cls, parser):
        """Add options for command line and config file."""
        parser.add_option('--putty-select', metavar='errors', default='',
                          help='putty select list')
        parser.add_option('--putty-ignore', metavar='errors', default='',
                          help='putty ignore list')
        parser.config_options.append('putty-select')
        parser.config_options.append('putty-ignore')

    @classmethod
    def parse_options(cls, options):
        """Parse options and activate `ignore_code` handler."""
        if not options.putty_select and not options.putty_ignore:
            return

        options._orig_select = options.select
        options._orig_ignore = options.ignore

        options.putty_select = Parser(options.putty_select)._rules
        options.putty_ignore = Parser(options.putty_ignore)._rules

        options.ignore_code = functools.partial(
            putty_ignore_code,
            options)

        options.report._ignore_code = options.ignore_code
