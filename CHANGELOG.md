# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

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
