# -*- coding: utf-8 -*-
"""Flake8 putty configuration."""
from __future__ import absolute_import, unicode_literals

import collections
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


class SelectorBase(object):

    """Base class for selectors."""

    _text = None

    _starts_with = None
    _ends_with = None

    __implementations__ = []

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

    def match(self, filename, line, codes):
        """Match rule."""
        # abstract method


Selector = SelectorBase


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

    def match(self, filename, line, codes):
        """Match selector against error parameters."""
        match = self.regex.search(line)
        if not match:
            return False

        if not codes or not match.lastindex:
            return True

        # Currently the group name must be 'codes'
        try:
            disabled_codes = match.group('codes')
        except IndexError:
            return True

        disabled_codes = _stripped_codes(disabled_codes)

        current_code = codes[-1]

        return current_code in disabled_codes


class FileSelector(Selector):

    """File selector."""

    _ends_with = ('/', '.py')

    @property
    def pattern(self):
        """Return file pattern."""
        return self.raw

    def match(self, filename, line, codes):
        """Match rule and set attribute codes."""
        if filename.startswith('.' + os.sep):
            filename = filename[len(os.sep) + 1:]
        if os.sep != '/':
            filename = filename.replace(os.sep, '/')

        if (self.pattern.endswith('/') and
                filename.startswith(self.pattern)):
            return True
        if fnmatch.fnmatch(filename, self.pattern):
            return True

        return False


class CodeSelector(Selector):

    """Existing code selector."""

    @property
    def code(self):
        """Return selector code."""
        return self.raw

    def match(self, filename, line, codes):
        """Match rule and set attribute codes."""
        if self.code in codes:
            return True
        return False


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


SelectorBase.__implementations__ = [
    CodeSelector,
    EnvironmentMarkerSelector,
    FileSelector,
    RegexSelector,
]


class RuleBase(object):

    """Rule to be used for matching."""

    _append_codes = None

    __implementations__ = []

    @classmethod
    def _use_cls(cls):
        # abstract method
        pass

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
        return '<{0} {1!r} : {2!r}>'.format(
            self.__class__.__name__,
            self._selectors,
            self.codes,
        )

    if sys.version_info[0] == 2:
        def __unicode__(self):
            return '%s : %s' % (self._selectors, self.codes)

        def __str__(self):
            return '%r' % self.__unicode__()

    else:
        def __str__(self):
            return '%s : %s' % (self._selectors, self.codes)


class Rule(RuleBase):

    """Rule implementing any."""

    @classmethod
    def _use_cls(cls, selectors):
        return True

    def __init__(self, selectors, codes):
        """Constructor."""
        self._grouped_selector = collections.defaultdict(list)
        for selector in selectors:
            self._grouped_selector[selector.__class__].append(selector)

        super(Rule, self).__init__(selectors, codes)

    def match(self, filename, line, codes):
        """Match rule and set attribute codes."""
        for cls, selectors in self._grouped_selector.items():
            if not any(x.match(filename, line, codes) for x in selectors):
                return False

        return True

    def codes_match_any(self, codes):
        """Old deprecated method."""
        return self.match('x', 'x', codes)

    def file_match_any(self, filename):
        """Old deprecated method."""
        return self.match(filename, 'x', 'x')


class RegexRule(Rule):

    """Rule that uses regexes."""

    @classmethod
    def _use_cls(cls, selectors):
        return any(isinstance(x, RegexSelector) for x in selectors)

    def __init__(self, selectors, codes):
        """Constructor."""
        self.regex_selectors = [
            selector for selector in selectors
            if isinstance(selector, RegexSelector)]

        super(RegexRule, self).__init__(selectors, codes)

        self._vary_codes = self.codes == ('(?P<codes>)', )

    def regex_match_any(self, line, codes=None):
        """Old deprecated method."""
        return self.match('x', line, codes)

    def match(self, filename, line, codes):
        """Match rule and set attribute codes."""
        rv = super(RegexRule, self).match(filename, line, codes)
        if rv:
            if self._vary_codes:
                self.codes = tuple([codes[-1]])
            return True


RuleBase.__implementations__ = [
    Rule,
    RegexRule,
]


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

        selector_classes = list(reversed(SelectorBase.__implementations__))
        rule_classes = list(reversed(RuleBase.__implementations__))

        self.__rules = []
        lines = self._parsed_lines()
        for i, _selectors, codes in lines:
            selectors = []
            for _selector in _selectors:
                for cls in selector_classes:
                    if cls._use_cls(_selector):
                        break
                else:
                    raise NotImplementedError(
                        'No class selector for "{0}"'.format(_selector),
                    )

                selector = cls(_selector)

                selectors.append(selector)

            rule = None
            for cls in rule_classes:
                if cls._use_cls(selectors):
                    rule = cls(selectors, codes)
                    break

            assert rule

            self.__rules.append(rule)

        return self.__rules
