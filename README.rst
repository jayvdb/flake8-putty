Flake8 Putty
============

.. image:: https://secure.travis-ci.org/jayvdb/flake8-putty.png?branch=master
   :alt: Build Status
   :target: https://travis-ci.org/jayvdb/flake8-putty

.. image:: http://codecov.io/github/jayvdb/flake8-putty/coverage.svg?branch=master
   :alt: Coverage Status
   :target: http://codecov.io/github/jayvdb/flake8-putty?branch=master

.. image:: https://landscape.io/github/jayvdb/flake8-putty/master/landscape.svg?style=flat
   :alt: Code Quality
   :target: https://landscape.io/github/jayvdb/flake8-putty

.. image:: https://badge.fury.io/py/flake8-putty.svg
   :alt: Pypi Entry
   :target: https://pypi.python.org/pypi/flake8-putty

Flake8 Putty allows more control over errors reported by flake8,
without adding noqa for every erroneous or undesirable error detected.

See https://gitlab.com/pycqa/flake8/issues/89 for some of the motivation
for this extension.

If you only want better `noqa` support,
`flake8-respect-noqa <https://pypi.python.org/pypi/flake8-respect-noqa>`_
is a simpler extension which works only when multiprocessing is disabled.

Disabling erroneous or undesirable errors by adding `noqa` in the code
may be undesirable for a number of reasons, including:

- the 'error' appears frequently
- the module is strictly in maintenance mode only
- it causes a line to break the line length rule
- the error should be ignored on only some versions or platforms

Installation
------------

Simply::

  $ pip install flake8-putty

Check that flake8 finds it::


  $ flake8 --version

  2.4.1 (pep8: 1.5.7, flake8-putty: 0.3.2, mccabe: 0.3.1, pyflakes: 0.8.1) CPython 2.7.6 on Linux

Usage
-----

flake8-putty is not activated unless `putty-auto-ignore`, `putty-ignore`
or `putty-select` appear in the configuration file or command line options.

Auto ignore detects comments on each line like `..  # flake8: disable=xxxx`.

`putty-ignore` and `putty-select` both support multiline values, and each
line is a rule which should have the format:

  <selectors> : <modifier><codes>

The codes are flake8 codes to use when the rule is matched.
The only modifier is `+` which appends the codes to the list of codes from
other rules.

Selectors may contain one or more of:
- file patterns
- line regexes
- flake8 codes

When multiple file pattern selectors are used, only one of the file patterns
needs to match the filename.
Likewise only one of many regex and only one of many codes needs to be matched.

However when different types of selectors are combined in one rule,
each type of selector must be matched.

e.g. when two filenames and two regex are used, at least one filename and one
regex must match before the rule is activated.

All matching rules are processed.

Examples
--------

Disable only D102 on foo.py

  putty-ignore =
    foo.py : D102

Disable D205, D400 and D401 for `__init__` methods:

  putty-ignore =
    /__init__/ : +D205,D400,D401

Disable T001 only when it is explicitly mentioned

  putty-ignore =
    /# !qa:.*T001/ : +T001

Disable any code that is explicitly mentioned

  putty-ignore =
    /# !qa: *(?P<codes>[A-Z0-9, ]*)/ : +(?P<codes>)

Disable any code that occurs after # flake8: disable=

  putty-auto-ignore = True
