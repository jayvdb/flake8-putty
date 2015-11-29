Flake8 Putty
============

Flake8 Putty allows more control over errors reported by flake8,
without adding noqa for every erroneous or undesirable error detected.

See https://gitlab.com/pycqa/flake8/issues/89 for some of the motivation
for this extension.

If you only want better `noqa` support, flake8-respect-noqa is a simpler
extension which works only when multiprocessing is disabled.

Disabling erroneous or undesirable errors by adding `noqa` in the code
may be undesirable for a number of reasons, including:

- the 'error' appears frequently
- the module is strictly in maintenance mode only
- it causes a line to break the line length rule

Installation
------------

Simply::

  $ pip install flake8-putty

Check that flake8 finds it::


  $ flake8 --version

  2.4.1 (pep8: 1.5.7, flake8-putty: 0.1.0, mccabe: 0.3.1, pyflakes: 0.8.1) CPython 2.7.6 on Linux

Usage
-----

flake8-putty is not activated unless `putty-ignore` or `putty-select` appear
in the configuration file or command line options.

`putty-ignore` and `putty-select` both support multiline values, and each
line is a rule which should have the format:

  <selectors> : <codes>

Selectors may contain one or more of:
- file patterns
- line regexes
- flake8 codes

When multiple file pattern selectors are used, only one of the file patterns
needs to match the filename.
Likewise only one of many regex and only one of many codes needs to be matched.
However types of selectors are combined, each type of selector must be matched.

e.g. when two filenames and two regex are used, at least one filename and one
regex must match before the rule is activated.

All matching rules are processed.

Examples
--------

Disable only D102 on foo.py

  putty-ignore =
    foo.py : D102

Disable T001 only when it is explicitly mentioned

  putty-ignore =
    /# !qa:.*T001/ : +T001

Disable D205, D400 and D401 for `__init__` methods:

  putty-ignore =
    /__init__/ : +D205,D400,D401
