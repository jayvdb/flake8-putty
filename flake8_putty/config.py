# -*- coding: utf-8 -*-
"""Flake8 putty configuration."""
from __future__ import absolute_import, unicode_literals

import fnmatch
import os
import re
import sys

try:
    from packaging import markers
except ImportError:
    markers = None

try:
    import globre
except ImportError:
    globre = None

IS_WINDOWS = (sys.platform == 'win32')

SELECTOR_SPLITTER = re.compile(r' *(/.*?(?<!\\)/|[^/][^,]*) *,?')

ENVIRONMENT_MARKER_PREFIXES = (
    'os_',
    'sys_',
    'platform_',
    'python_',
    'implementation_',
)


def _stripped_codes(codes):
    """Return a tuple of stripped codes split by ','."""
    return tuple(
        code.strip() for code in codes.split(',')
        if code.strip(),
    )


class Selector(object):

    """Base class for selectors."""

    _text = None

    _starts_with = None
    _ends_with = None

    @classmethod
    def _use_cls(cls, text):
        if cls._ends_with and not text.endswith(cls._ends_with):
            return False
        
        if cls._starts_with and not text.startswith(cls._starts_with):
            return False

        return True

    def __init__(self, text=None):
        """Constructor."""
        if text is not None:
            self._text = text

    @property
    def raw(self):
        """Return raw selector text."""
        return self._text

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self._text == other.raw

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._text)


class RegexSelector(Selector):

    """Regex selector."""

    _starts_with = _ends_with = '/'

    def __init__(self, text=None):
        """Constructor."""
        if text and text[0] == '/':
            text = text[1:-1]
        self._compiled_regex = None
        super(RegexSelector, self).__init__(text)

    @property
    def regex(self):
        """Return compiled regex."""
        if not self._compiled_regex:
            self._compiled_regex = re.compile(self.raw)
        return self._compiled_regex


class FileSelector(Selector):

    """File selector."""

    _ends_with = ('/', '.py')

    @property
    def pattern(self):
        """Return file pattern."""
        return self.raw


class CodeSelector(Selector):

    """Existing code selector."""

    @property
    def code(self):
        """Return selector code."""
        return self.raw


class EnvironmentMarkerSelector(Selector):

    """Existing code selector."""

    _starts_with = ENVIRONMENT_MARKER_PREFIXES

    def __init__(self, text):
        """Constructor."""
        self._marker = None
        super(EnvironmentMarkerSelector, self).__init__(text)

    @property
    def marker(self):
        """Return environment marker."""
        if not self._marker:
            assert markers, 'Package packaging is needed for environment markers'
            self._marker = markers.Marker(self.raw)
        return self._marker

    def evaluate(self, environment=None):
        """Evaluate the environment marker."""
        return self.marker.evaluate(environment)


SELECTOR_CLASSES = [
    CodeSelector,
    EnvironmentMarkerSelector,
    FileSelector,
    RegexSelector,
]


class RuleBase(object):

    """Rule to be used for matching."""

    _append_codes = None

    def __init__(self, selectors, codes):
        """Constructor."""
        self._selectors = selectors

        codes = codes.strip()
        if codes.startswith('+'):
            self._append_codes = True
            codes = codes[1:]
        else:
            self._append_codes = False

        self.codes = _stripped_codes(codes)

    def match(self, filename, line, codes):
        """Match rule."""
        # abstract method

    @property
    def all_selectors(self):
        """Iterable of all selectors."""
        return self._selectors

    def __eq__(self, other):
        """True if other is instance of Rule with same codes and selectors."""
        if isinstance(other, self.__class__):
            return ((self._selectors, self.codes) ==
                    (other.all_selectors, other.codes))

        return False

    def __repr__(self):
        return '<Rule %r : %r>' % (self._selectors, self.codes)

    if sys.version_info[0] == 2:
        def __unicode__(self):
            return '%s : %s' % (self._selectors, self.codes)

        def __str__(self):
            return '%r' % self.__unicode__()

    else:
        def __str__(self):
            return '%s : %s' % (self._selectors, self.codes)


class RegexRule(RuleBase):

    """Rule that uses regexes."""

    def __init__(self, selectors, codes):
        """Constructor."""
        self.regex_selectors = [
            selector for selector in selectors
            if isinstance(selector, RegexSelector)]

        super(RegexRule, self).__init__(selectors, codes)

        self._vary_codes = self.codes == ('(?P<codes>)', )

    def regex_match_any(self, line, codes=None):
        """Match any regex."""
        for selector in self.regex_selectors:
            match = selector.regex.search(line)
            if match:
                if codes and match.lastindex:
                    # Currently the group name must be 'codes'
                    try:
                        disabled_codes = match.group('codes')
                    except IndexError:
                        return True

                    disabled_codes = _stripped_codes(disabled_codes)

                    current_code = codes[-1]

                    if current_code in disabled_codes:
                        return True
                else:
                    return True
        return False

    def match(self, filename, line, codes):
        """Match rule and set attribute codes."""
        if self.regex_selectors:
            if self.regex_match_any(line, codes):
                if self._vary_codes:
                    self.codes = tuple([codes[-1]])
                return True

        return super(RegexRule, self).match(filename, line, codes)


class FileRule(RuleBase):

    """Rule that uses match against files."""

    def __init__(self, selectors, codes):
        """Constructor."""
        self.file_selectors = [
            selector for selector in selectors
            if isinstance(selector, FileSelector)]

        super(FileRule, self).__init__(selectors, codes)

    def file_match_any(self, filename):
        """Match any filename."""
        if filename.startswith('.' + os.sep):
            filename = filename[len(os.sep) + 1:]
        if os.sep != '/':
            filename = filename.replace(os.sep, '/')

        for selector in self.file_selectors:
            if (selector.pattern.endswith('/') and
                    filename.startswith(selector.pattern)):
                return True
            if fnmatch.fnmatch(filename, selector.pattern):
                return True
        return False

    def match(self, filename, line, codes):
        """Match rule and set attribute codes."""
        if self.file_selectors:
            if self.file_match_any(filename):
                return True

        return super(FileRule, self).match(filename, line, codes)


class CodeRule(RuleBase):

    def __init__(self, selectors, codes):
        """Constructor."""
        self.code_selectors = [
            selector for selector in selectors
            if isinstance(selector, CodeSelector)]

        super(CodeRule, self).__init__(selectors, codes)

    def codes_match_any(self, codes):
        """Match any code."""
        for selector in self.code_selectors:
            if selector.code in codes:
                return True
        return False

    def match(self, filename, line, codes):
        """Match rule and set attribute codes."""
        if self.code_selectors:
            if self.codes_match_any(codes):
                return True

        return super(CodeRule, self).match(filename, line, codes)


class EnvironmentMarkerRule(RuleBase):

    def __init__(self, selectors, codes):
        """Constructor."""
        environment_marker_selectors = [
            selector for selector in selectors
            if isinstance(selector, EnvironmentMarkerSelector)]
        assert len(environment_marker_selectors) < 2
        if environment_marker_selectors:
            self.environment_marker_selector = environment_marker_selectors[0]
        else:
            self.environment_marker_selector = None

        super(EnvironmentMarkerRule, self).__init__(selectors, codes)

    def environment_marker_evaluate(self):
        """Evaluate the environment marker."""
        if self.environment_marker_selector:
            if self.environment_marker_selector.evaluate():
                return True
        return False

    def match(self, filename, line, codes):
        """Match rule and set attribute codes."""
        if self.environment_marker_selector:
            if self.environment_marker_evaluate():
                return True

        return super(EnvironmentMarkerRule, self).match(filename, line, codes)


class Rule(FileRule, RegexRule, CodeRule, EnvironmentMarkerRule):

    """Rule containing selectors and codes to be used."""



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
            selectors = [selector.strip() for selector in selectors]

            yield i, selectors, codes

    @property
    def _rules(self):
        if self.__rules is not None:
            return self.__rules

        selector_classes = list(reversed(SELECTOR_CLASSES))

        self.__rules = []
        lines = self._parsed_lines()
        for i, _selectors, codes in lines:
            selectors = []
            for _selector in _selectors:
                for cls in selector_classes:
                    if cls._use_cls(_selector):
                        break
                else:
                    # TODO: warning
                    continue

                print('found', cls)

                selector = cls(_selector)

                selectors.append(selector)

            self.__rules.append(Rule(selectors, codes))

        return self.__rules
