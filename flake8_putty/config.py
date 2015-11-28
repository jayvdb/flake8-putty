# -*- coding: utf-8 -*-
"""Flake8 putty configuration."""
from __future__ import unicode_literals

import fnmatch
import os
import re
import sys

SELECTOR_SPLITTER = re.compile(r' *(/.*?(?<!\\)/|[^/][^,]*) *,?')


class Selector(object):

    """Base class for selectors."""

    def __init__(self, text):
        """Constructor."""
        self._text = text

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self._text == other._text

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._text)


class RegexSelector(Selector):

    """Regex selector."""

    def __init__(self, text):
        """Constructor."""
        self._compiled_regex = None
        super(RegexSelector, self).__init__(text)

    @property
    def raw(self):
        """Return raw regex."""
        return self._text

    @property
    def regex(self):
        """Return compiled regex."""
        if not self._compiled_regex:
            self._compiled_regex = re.compile(self._text)
        return self._compiled_regex


class FileSelector(Selector):

    """File selector."""

    @property
    def pattern(self):
        """Return file pattern."""
        return self._text


class CodeSelector(Selector):

    """Existing code selector."""

    @property
    def code(self):
        """Return selector code."""
        return self._text


class Rule(object):

    """Rule containing selectors and codes to be used."""

    def __init__(self, selectors, codes):
        """Constructor."""
        self._selectors = selectors
        self.file_selectors = [
            selector for selector in selectors
            if isinstance(selector, FileSelector)]
        self.regex_selectors = [
            selector for selector in selectors
            if isinstance(selector, RegexSelector)]
        self.code_selectors = [
            selector for selector in selectors
            if isinstance(selector, CodeSelector)]

        codes = codes.strip()
        if codes.startswith('+'):
            self._append_codes = True
            codes = codes[1:]
        else:
            self._append_codes = False

        self.codes = tuple(
            code.strip() for code in codes.split(',')
            if code.strip())

    def __eq__(self, other):
        return (self._selectors, self.codes) == (other._selectors, other.codes)

    def file_match_any(self, filename):
        """Match any filename."""
        if filename.startswith('.' + os.sep):
            filename = filename[2:]
        for selector in self.file_selectors:
            if fnmatch.fnmatch(filename, selector.pattern):
                return True
        return False

    def regex_match_any(self, line):
        """Match any regex."""
        for selector in self.regex_selectors:
            if selector.regex.search(line):
                return True
        return False

    def codes_match_any(self, codes):
        """Match any code."""
        for selector in self.code_selectors:
            if selector.code in codes:
                return True
        return False

    def match(self, filename, line, codes):
        """Match rule."""
        return ((not self.file_selectors or self.file_match_any(filename)) and
                (not self.regex_selectors or self.regex_match_any(line)) and
                (not self.code_selectors or self.codes_match_any(codes)))

    def __repr__(self):
        return '<Rule %r : %r' % (self._selectors, self.codes)

    if sys.version_info[0] == 2:
        def __unicode__(self):
            return '%s : %s' % (self._selectors, self.codes)

        def __str__(self):
            return '%r' % self.__unicode__()

    else:
        def __str__(self):
            return '%s : %s' % (self._selectors, self.codes)


class Parser(object):

    """Config option parser."""

    def __init__(self, text):
        """Constructor."""
        self.text = text
        self.__rules = None

    def _lines(self):
        lines = self.text.splitlines()
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            yield i, line

    def _parsed_lines(self):
        lines = self._lines()
        for i, line in lines:
            if ':' not in line:
                pass
            try:
                selectors, codes = line.rsplit(' : ', 1)
            except RuntimeError:
                selectors, codes = line.rsplit(':', 1)

            assert selectors
            assert codes

            selectors = SELECTOR_SPLITTER.findall(selectors)

            yield i, selectors, codes

    @property
    def _rules(self):
        if self.__rules is not None:
            return self.__rules

        self.__rules = []
        lines = self._parsed_lines()
        for i, _selectors, codes in lines:
            selectors = []
            for _selector in _selectors:
                if _selector.startswith('/') and _selector.endswith('/'):
                    selector = RegexSelector(_selector[1:-1])
                elif _selector.endswith('.py') or _selector.endswith('/'):
                    selector = FileSelector(_selector)
                else:
                    selector = CodeSelector(_selector)
                selectors.append(selector)

            self.__rules.append(Rule(selectors, codes))
        return self.__rules
