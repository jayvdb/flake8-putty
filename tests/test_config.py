# -*- coding: utf-8 -*-
"""Test config parser."""
from __future__ import unicode_literals

from unittest import TestCase

from flake8_putty.config import (
    CodeSelector,
    FileSelector,
    Parser,
    RegexSelector,
    Rule,
)


class TestParser(TestCase):

    """Test config option rule parser."""

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

    def test_mixed(self):
        p = Parser('/(a, b)/ , C001, foo.py : E101')

        assert list(p._parsed_lines()) == [
            (1, ['/(a, b)/', 'C001', 'foo.py'], 'E101'),
        ]

        assert p._rules == [
            Rule([RegexSelector('(a, b)'),
                  CodeSelector('C001'),
                  FileSelector('foo.py')],
                 'E101'),
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


class TestMatch(TestCase):

    """Test config option rule parser."""

    def test_selector_filename(self):
        p = Parser('foo.py : E101')
        assert p._rules[0].file_match_any('foo.py')
        assert p._rules[0].file_match_any('./foo.py')
        assert not p._rules[0].file_match_any('bar.py')
        assert not p._rules[0].file_match_any('foo/bar.py')

    def test_selector_filename_multi(self):
        p = Parser('foo.py, bar.py : E101')
        assert p._rules[0].file_match_any('foo.py')
        assert p._rules[0].file_match_any('./foo.py')
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
        assert p._rules[0].file_match_any('./tests/foo/bar/test_baz.py')
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
