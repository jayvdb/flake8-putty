# -*- coding: utf-8 -*-
"""Test config parser."""
from __future__ import unicode_literals

import os

try:
    from unittest2 import TestCase, SkipTest
except ImportError:
    from unittest import TestCase, SkipTest

from flake8_putty.config import (
    CodeSelector,
    EnvironmentMarkerSelector,
    FileSelector,
    Parser,
    RegexSelector,
    Rule,
    markers,
)
from flake8_putty.extension import AutoLineDisableRule


class TestParser(TestCase):

    """Test config option rule parser."""

    def test_selector_comment_empty_line(self):
        p = Parser('# foo')
        assert list(p._lines()) == []

    def test_selector_comment_suffix(self):
        p = Parser('E100 : E101 # foo')
        assert list(p._lines()) == [
            (1, 'E100 : E101 # foo'),
        ]

        assert list(p._parsed_lines()) == [
            (1, ['E100'], 'E101'),
        ]

        assert p._rules == [
            Rule([CodeSelector('E100')], 'E101'),
        ]

    def test_selector_code(self):
        p = Parser('E100 : E101')
        assert list(p._lines()) == [
            (1, 'E100 : E101'),
        ]

        assert list(p._parsed_lines()) == [
            (1, ['E100'], 'E101'),
        ]

        assert p._rules == [
            Rule([CodeSelector('E100')], 'E101'),
        ]

    def test_selector_code_multi(self):
        p = Parser('E100, E200 : E101')
        assert list(p._lines()) == [
            (1, 'E100, E200 : E101'),
        ]

        assert list(p._parsed_lines()) == [
            (1, ['E100', 'E200'], 'E101'),
        ]

        assert p._rules == [
            Rule([CodeSelector('E100'), CodeSelector('E200')], 'E101'),
        ]

    def test_selector_marker(self):
        p = Parser("python_version == '2.4' : E101")
        assert list(p._lines()) == [
            (1, "python_version == '2.4' : E101"),
        ]

        assert list(p._parsed_lines()) == [
            (1, ["python_version == '2.4'"], 'E101'),
        ]

        assert p._rules == [
            Rule(
                [EnvironmentMarkerSelector("python_version == '2.4'")],
                'E101',
            ),
        ]

    def test_selector_filename(self):
        p = Parser('foo.py : E101')
        assert list(p._lines()) == [
            (1, 'foo.py : E101'),
        ]

        assert list(p._parsed_lines()) == [
            (1, ['foo.py'], 'E101'),
        ]

        assert p._rules == [
            Rule([FileSelector('foo.py')], 'E101'),
        ]

    def test_selector_dir(self):
        p = Parser('tests/ : E101')
        assert list(p._lines()) == [
            (1, 'tests/ : E101'),
        ]

        assert list(p._parsed_lines()) == [
            (1, ['tests/'], 'E101'),
        ]

        assert p._rules == [
            Rule([FileSelector('tests/')], 'E101'),
        ]

    def test_selector_filename_multi(self):
        p = Parser('foo.py, bar.py : E101')
        assert list(p._lines()) == [
            (1, 'foo.py, bar.py : E101'),
        ]

        assert list(p._parsed_lines()) == [
            (1, ['foo.py', 'bar.py'], 'E101'),
        ]

        assert p._rules == [
            Rule([FileSelector('foo.py'), FileSelector('bar.py')], 'E101'),
        ]

    def test_selector_filename_explicit_relative(self):
        p = Parser('./foo.py : E101')
        assert list(p._lines()) == [
            (1, './foo.py : E101'),
        ]

        assert list(p._parsed_lines()) == [
            (1, ['./foo.py'], 'E101'),
        ]

        assert p._rules == [
            Rule([FileSelector('./foo.py')], 'E101'),
        ]

    def test_selector_explicit_relative_dir(self):
        p = Parser('./ : E101')
        assert list(p._lines()) == [
            (1, './ : E101'),
        ]

        assert list(p._parsed_lines()) == [
            (1, ['./'], 'E101'),
        ]

        assert p._rules == [
            Rule([FileSelector('./')], 'E101'),
        ]

    def test_selector_explicit_relative_star(self):
        p = Parser('./* : E101')
        assert list(p._lines()) == [
            (1, './* : E101'),
        ]

        assert list(p._parsed_lines()) == [
            (1, ['./*'], 'E101'),
        ]

        # TODO(#9): This should be a FileSelector, not a CodeSelector
        assert p._rules == [
            Rule([CodeSelector('./*')], 'E101'),
        ]

    def test_selector_star(self):
        p = Parser('* : E101')
        assert list(p._lines()) == [
            (1, '* : E101'),
        ]

        assert list(p._parsed_lines()) == [
            (1, ['*'], 'E101'),
        ]

        # TODO(#9): This is a CodeSelector, which isnt suitable,
        # but a good purpose for this has not been established.
        assert p._rules == [
            Rule([CodeSelector('*')], 'E101'),
        ]

    def test_selector_regex(self):
        p = Parser('/foo/ : E101')
        assert list(p._lines()) == [
            (1, '/foo/ : E101'),
        ]

        assert list(p._parsed_lines()) == [
            (1, ['/foo/'], 'E101'),
        ]

        assert p._rules == [
            Rule([RegexSelector('foo')], 'E101'),
        ]

    def test_selector_regex_hash(self):
        p = Parser('/# noqa/ : E101')
        assert list(p._lines()) == [
            (1, '/# noqa/ : E101'),
        ]

        assert list(p._parsed_lines()) == [
            (1, ['/# noqa/'], 'E101'),
        ]

        assert p._rules == [
            Rule([RegexSelector('# noqa')], 'E101'),
        ]

    def test_selector_regex_colon(self):
        p = Parser('/if.*:/ : E101')
        assert list(p._lines()) == [
            (1, '/if.*:/ : E101'),
        ]

        assert list(p._parsed_lines()) == [
            (1, ['/if.*:/'], 'E101'),
        ]

    def test_selector_regex_comma(self):
        p = Parser('/(a, b)/ : E101')
        assert list(p._lines()) == [
            (1, '/(a, b)/ : E101'),
        ]

        assert list(p._parsed_lines()) == [
            (1, ['/(a, b)/'], 'E101'),
        ]

        assert p._rules == [
            Rule([RegexSelector('(a, b)')], 'E101'),
        ]

    def test_selector_regex_multi(self):
        p = Parser('/(a, b)/ , /(c, d)/ : E101')
        assert list(p._lines()) == [
            (1, '/(a, b)/ , /(c, d)/ : E101'),
        ]

        assert list(p._parsed_lines()) == [
            (1, ['/(a, b)/', '/(c, d)/'], 'E101'),
        ]

        assert p._rules == [
            Rule([RegexSelector('(a, b)'), RegexSelector('(c, d)')], 'E101'),
        ]

    def test_selector_regex_codes(self):
        p = Parser('/# !qa: *(?P<codes>[A-Z0-9, ]*)/ : (?P<codes>)')

        assert list(p._lines()) == [
            (1, '/# !qa: *(?P<codes>[A-Z0-9, ]*)/ : (?P<codes>)'),
        ]

        assert list(p._parsed_lines()) == [
            (1, ['/# !qa: *(?P<codes>[A-Z0-9, ]*)/'], '(?P<codes>)'),
        ]

        assert p._rules == [
            Rule(
                [RegexSelector('# !qa: *(?P<codes>[A-Z0-9, ]*)')],
                '(?P<codes>)',
            ),
        ]

    def test_selector_regex_codes_append(self):
        p = Parser('/# !qa: *(?P<codes>[A-Z0-9, ]*)/ : +(?P<codes>)')

        assert list(p._lines()) == [
            (1, '/# !qa: *(?P<codes>[A-Z0-9, ]*)/ : +(?P<codes>)'),
        ]

        assert list(p._parsed_lines()) == [
            (1, ['/# !qa: *(?P<codes>[A-Z0-9, ]*)/'], '+(?P<codes>)'),
        ]

        assert p._rules == [
            Rule(
                [RegexSelector('# !qa: *(?P<codes>[A-Z0-9, ]*)')],
                '(?P<codes>)',
            ),
        ]

    def test_mixed(self):
        p = Parser('/(a, b)/ , C001, foo.py : E101')

        assert list(p._parsed_lines()) == [
            (1, ['/(a, b)/', 'C001', 'foo.py'], 'E101'),
        ]

        assert p._rules == [
            Rule(
                [
                    RegexSelector('(a, b)'),
                    CodeSelector('C001'),
                    FileSelector('foo.py'),
                ],
                'E101',
            ),
        ]

        p = Parser('foo.py , /def foo/ : +E101')

        assert list(p._parsed_lines()) == [
            (1, ['foo.py', '/def foo/'], '+E101'),
        ]

        assert p._rules == [
            Rule(
                [FileSelector('foo.py'), RegexSelector('def foo')],
                'E101',
            ),
        ]

    def test_multiline(self):
        p = Parser("""
        E100 : E101
        """)
        assert list(p._parsed_lines()) == [
            (2, ['E100'], 'E101'),
        ]

        p = Parser("""
        E100 : E101
        E200 : E201
        """)
        assert list(p._parsed_lines()) == [
            (2, ['E100'], 'E101'),
            (3, ['E200'], 'E201'),
        ]

    def test_multiple_codes(self):
        p = Parser("""
        E100, E101 : E200, E201
        """)
        assert list(p._parsed_lines()) == [
            (2, ['E100', 'E101'], 'E200, E201'),
        ]


class TestMatchFilename(TestCase):

    """Test matching filenames."""

    def test_selector_filename(self):
        p = Parser('foo.py : E101')
        assert p._rules[0].file_match_any('foo.py')
        assert p._rules[0].file_match_any('.{0}foo.py'.format(os.sep))
        assert not p._rules[0].file_match_any('bar.py')
        assert not p._rules[0].file_match_any('foo/bar.py')

    def test_selector_filename_missing(self):
        """Test that file_match_any isnt True if there are no filename rules."""
        p = Parser('/foo/ : E101')
        assert not p._rules[0].file_match_any(' foo ')

    def test_selector_filename_multi(self):
        p = Parser('foo.py, bar.py : E101')
        assert p._rules[0].file_match_any('foo.py')
        assert p._rules[0].file_match_any('.{0}foo.py'.format(os.sep))
        assert p._rules[0].file_match_any('bar.py')
        assert not p._rules[0].file_match_any('foo/bar.py')

    def test_selector_directory(self):
        p = Parser('tests/ : E101')
        assert p._rules[0].file_match_any('tests/foo.py')
        assert not p._rules[0].file_match_any('other/foo.py')

    def test_selector_directory_multi(self):
        p = Parser('tests/, vendor/ : E101')
        assert p._rules[0].file_match_any('tests/foo.py')
        assert p._rules[0].file_match_any('vendor/foo.py')
        assert not p._rules[0].file_match_any('other/foo.py')

    def test_selector_directory_wildcard(self):
        p = Parser('tests/*/test_*.py : E101')
        assert p._rules[0].file_match_any('tests/foo/test_bar.py')
        assert p._rules[0].file_match_any(
            '.{0}tests/foo/bar/test_baz.py'.format(os.sep),
        )
        assert p._rules[0].file_match_any('tests/foo/bar/test_.py')
        assert not p._rules[0].file_match_any('tests/test_foo.py')

    def test_selector_directory_wildcard_nested(self):
        p = Parser('tests/*/*/test_*.py : E101')
        assert p._rules[0].file_match_any('tests/foo/bar/test_baz.py')
        assert not p._rules[0].file_match_any('tests/foo/test_bar.py')

    def test_selector_directory_wildcard_multi(self):
        p = Parser('tests/*/test_*.py, vendor/*/test_*.py : E101')
        assert p._rules[0].file_match_any('tests/foo/test_bar.py')
        assert p._rules[0].file_match_any('vendor/foo/test_bar.py')
        assert not p._rules[0].file_match_any('other/foo/test_bar.py')


class TestMatchRegex(TestCase):

    """Test matching source lines."""

    def test_selector_regex(self):
        p = Parser('/foo/ : E101')
        assert p._rules[0].regex_match_any(' foo bar ')
        assert not p._rules[0].regex_match_any(' bar ')

    def test_selector_regex_multi(self):
        p = Parser('/foo/ , /bar/ : E101')
        assert p._rules[0].regex_match_any(' foo bar ')
        assert p._rules[0].regex_match_any(' bar ')
        assert not p._rules[0].regex_match_any(' baz ')

    def test_selector_regex_codes(self):
        p = Parser('/# !qa: *(?P<codes>[A-Z0-9, ]*)/ : (?P<codes>)')
        assert p._rules[0].regex_match_any(' foo bar # !qa: E101', ['E101'])
        assert not p._rules[0].regex_match_any(' baz # !qa: E101', ['E102'])

    def test_selector_regex_codes_append(self):
        p = Parser('/# !qa: *(?P<codes>[A-Z0-9, ]*)/ : +(?P<codes>)')
        assert p._rules[0].regex_match_any(' foo bar # !qa: E101', ['E101'])
        assert not p._rules[0].regex_match_any(' baz # !qa: E101', ['E102'])

    def test_selector_regex_codes_multi(self):
        p = Parser('/# !qa: *(?P<codes>[A-Z0-9, ]*)/ : +(?P<codes>)')
        assert p._rules[0].regex_match_any(
            ' foo bar # !qa: E101, E102',
            ['E101'],
        )
        assert p._rules[0].regex_match_any(
            ' foo bar # !qa: E101, E102',
            ['E102'],
        )

    def test_selector_regex_codes_multi_match(self):
        p = Parser('/disable=(?P<codes>[A-Z0-9]*)/ : +(?P<codes>)')
        assert p._rules[0].regex_match_any(
            ' foo bar # disable=E101 disable=E102',
            ['E101'],
        )
        assert p._rules[0].regex_match_any(
            ' foo bar # disable=E101 disable=E102',
            ['E102'],
        )

    def test_selector_auto(self):
        rule = AutoLineDisableRule()
        assert rule.regex_match_any('foo # flake8: disable=E101', ['E101'])
        assert not rule.regex_match_any('foo # flake8: disable=E101', ['E102'])

    def test_selector_auto_missing_code(self):
        rule = AutoLineDisableRule()
        assert not rule.regex_match_any('foo # flake8: disable=', ['E101'])
        assert not rule.regex_match_any('foo # flake8: disable=', ['E102'])

    def test_selector_auto_multi(self):
        rule = AutoLineDisableRule()
        assert rule.regex_match_any('# flake8: disable=E101, E102', ['E101'])
        assert rule.regex_match_any('# flake8: disable=E101, E102', ['E102'])
        assert not rule.regex_match_any('# flake8: disable=E10', ['E102'])

    def test_selector_auto_unrelated(self):
        rule = AutoLineDisableRule()
        assert rule.regex_match_any(
            '# flake8: disable=E101 pylint: disable=E102', ['E101'],
        )
        assert not rule.regex_match_any(
            '# flake8: disable=E101 pylint: disable=E102', ['E102'],
        )
        assert rule.regex_match_any(
            '# pylint: disable=E102 flake8: disable=E101', ['E101'],
        )
        assert not rule.regex_match_any(
            '# pylint: disable=E102 flake8: disable=E101', ['E102'],
        )

    def test_combined_selectors(self):
        p = Parser('test.py, /foo/ : E101')
        assert p._rules[0].match('test.py', 'def foo', ['n/a'])


class TestMatchEnvironmentMarker(TestCase):

    """Test matching environment markers."""

    @classmethod
    def setUpClass(cls):
        if not markers:
            raise SkipTest('Package packaging not found')

    def test_selector_environment_marker(self):
        p = Parser("python_version == '2.4' : E101")
        assert not p._rules[0].environment_marker_evaluate()

        p = Parser("python_version > '2.4' : E101")
        assert p._rules[0].environment_marker_evaluate()
