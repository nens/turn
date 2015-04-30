todo
----

- Make reset perform a bump first. This shortens the tests further, too.
- Test kill -9
- Really tough tests, starting three locks simultanously and crash and
  kill any of them, checking no overlapping resource access.
- remove the test tool as it has been superseeded by said tough tests
- Sphinx docs via docstrings
