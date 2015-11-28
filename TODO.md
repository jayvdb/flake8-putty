# TODO

1. test scenario: if one code is reported (e.g. print_function exists),
   ignore it and other codes (print function)

2. support control of any flake8 option, such as `max_line_length`,
   probably by replacing putty-ignore and putty-select with action syntax
   in the second component of each rule, i.e. `foo.py : ignore += D201` and
   `foo.py : max_line_length = 100`

3. create a trigger code for 'module has no code', which can be used to
   disable other codes.  i.e generic solution to
   https://github.com/savoirfairelinux/flake8-copyright/issues/1
