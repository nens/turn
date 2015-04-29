todo
----

- Test kill -9
- Sphinx docs via docstrings
- Make reset perform a bump first.
- Make optional test modes for the core keeper (quick first expire,
  or something else) and the reset tool (longer watch for guaranteed
  crash). Both actions can speed up the tests
- Really tough tests, starting three locks simultanously and crash and
  kill any of them, checking no overlapping resource access.
- remove the test tool as it has been superseeded by said tough tests
