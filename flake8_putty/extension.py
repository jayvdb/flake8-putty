# -*- coding: utf-8 -*-
"""Flake8 putty extension."""
from __future__ import absolute_import, unicode_literals

import ast
import functools
import sys
import tokenize

import pep8

from flake8_putty.config import Parser, RegexRule, RegexSelector

try:
    from enum import Enum
except ImportError:
    from enum34 import Enum


class Flake8CheckerType(Enum):

    """Flake8 checker types."""

    ast = 1
    physical = 2
    logical = 3


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


def _get_checker_state(depth=1):
    # Stack
    # 1. this function
    # ... depth
    # 3. QueueReport.error or pep8.StandardReport.error for flake8 -j 1
    # 4. pep8.Checker.check_(ast|physical|logical)
    # ... check_physical *usually* has extra stack frames,
    #     but the last physical line is called from check_all.
    # 5. pep8.Checker.check_all
    check_type = None

    frame = sys._getframe(3 + depth)

    # print('stack 4:', frame.f_locals)

    pep8_checker = frame.f_locals['self']
    assert isinstance(pep8_checker, pep8.Checker)

    if 'checker' in frame.f_locals:
        check_type = Flake8CheckerType.ast
        flake8_checker = frame.f_locals['checker']
        tree = frame.f_locals['tree']
        assert isinstance(tree, ast.Module)
    else:
        tree = None
        flake8_checker = frame.f_locals['check']
        if 'mapping' in frame.f_locals:
            check_type = Flake8CheckerType.logical
        else:
            check_type = Flake8CheckerType.physical

    return pep8_checker, check_type, flake8_checker, tree


def get_reporter_state():
    """Get pep8 reporter state from stack."""
    # Stack
    # 1. get_reporter_state (i.e. this function)
    # 2. putty_ignore_code
    # 3. QueueReport.error or pep8.StandardReport.error for flake8 -j 1
    frame = sys._getframe(3)

    reporter = frame.f_locals['self']
    assert isinstance(reporter, pep8.BaseReport)

    line_number = frame.f_locals['line_number']
    offset = frame.f_locals['offset']
    text = frame.f_locals['text']
    check = frame.f_locals['check']
    return reporter, line_number, offset, text, check


def _extract_logical_comments(tokens):
    return '\n'.join(t[1] for t in tokens if t[0] == tokenize.COMMENT)


def _deferred_logical_check(line_number,
                            error_line_number,
                            error_offset,
                            error_code, error_text,
                            pep8_checker,
                            error_id):
    """Re-report an error during the logical checks phase."""
    if line_number >= error_line_number:
        yield (
            (error_line_number, error_offset),
            '{0}: {1}'.format(error_code, error_text),
        )
        removed_check_list = [
            (name, checker, arguments)
            for name, checker, arguments in pep8_checker._logical_checks
            if name != error_id
        ]
        pep8_checker._logical_checks[:] = removed_check_list


def _get_name(obj):
    try:
        name = obj.__class__.__name__
    except AttributeError:
        name = obj.__name__
    return name


def putty_ignore_code(options, code):
    """Hook for pep8 'ignore_code'."""
    def _do_defer():
        name = _get_name(flake8_checker)
        error_id = 'deferred_{0}_{1}'.format(name, line_number)
        check_entry = (
            error_id,
            functools.partial(
                _deferred_logical_check,
                error_line_number=line_number,
                error_offset=offset,
                error_code=code,
                error_text=text,
                pep8_checker=pep8_checker,
                error_id=error_id,
            ),
            ['line_number'],
        )

        pep8_checker._logical_checks.append(check_entry)

    reporter, line_number, offset, text, check = get_reporter_state()
    invalid_line_number = line_number > len(reporter.lines)
    try:
        line = reporter.lines[line_number - 1]
    except IndexError:
        line = ''

    text = text[5:].strip()

    pep8_checker, check_type, flake8_checker, tree = _get_checker_state()

    options.ignore = options._orig_ignore
    options.select = options._orig_select

    for rule in options.putty_ignore:
        if (not invalid_line_number and
                (rule._logical_comments or rule._logical_line)):
            if check_type != Flake8CheckerType.logical:
                _do_defer()
                # always ignore
                return True
            elif rule._logical_comments:
                rule_line = _extract_logical_comments(pep8_checker.tokens)
            elif rule._logical_line:
                rule_line = pep8_checker.logical_line
        else:
            rule_line = line

        if rule.match(reporter.filename, rule_line, list(reporter.counters) + [code]):
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

    _append_codes = True
    _logical_comments = True

    def __init__(self):
        """Constructor."""
        super(AutoLineDisableRule, self).__init__(
            [AutoLineDisableSelector()],
            ['(?P<codes>)'],
        )

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
            '--putty-auto-ignore', action='store_true',
            help=('putty auto ignore lines matching '
                  '# flake8: disable=<code>,<code>'),
        )
        parser.config_options.append('putty-select')
        parser.config_options.append('putty-ignore')
        parser.config_options.append('putty-auto-ignore')

    @classmethod
    def parse_options(cls, options):
        """Parse options and activate `ignore_code` handler."""
        if not options.putty_select and not options.putty_ignore:
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
