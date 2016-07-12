# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## [0.4.0] - 2016-07-12
- Microsoft Windows filename selector fixes, with Appveyor CI testing (a0c7c604)
- Allow multiple codes to be disabled by per-line comments (4d5b9001)
- Allow comment after each rule line (1220229e)
- Prevent use with flake8 v3 (19bc89a1)
- Support both pep8 and pycodestyle in test suite (4d2e1530)

## [0.3.2] - 2016-04-08
- Fix regex selector matching multiple codes

## [0.3.1] - 2016-04-07
- Fix predefined ignore pattern

## [0.3.0] - 2016-04-06
- Allow regex selector to use codes extracted from each line
- Add predefined ignore pattern `# flake8: disable=<codes>`
- Add environment marker selector (PEP 0496)
- Fix bug when filename selector contained trailing whitespace
- Switched to using tox-travis, and added PyPy 3 testing

## [0.2.0] - 2015-12-01
- Fix bug when checker provides invalid line number
- Support directory selector
- Tested with flake8 2.2.0-2.5.0

## [0.1.0] - 2015-11-28
- Initial release
- Customisable ignore and select lists using filename pattern and regex selectors
