Overview
========

Script that uses the LiquidPlanner API to extract timesheet data.


Dependencies
------------

Interpreter:

 - Python 2.7

The script also requires the ``iso8601`` package and optionally (for
HTML output) the ``Chameleon`` package.

Both can be installed using setuptools::

  $ easy_install-2.7 iso8601
  $ easy_install-2.7 Chameleon


Usage
-----

Example::

  $ lptimesheet.py foo@hotmail.com myproj 1980/01/01 2050/12/31 --format html \
    > timesheet.html

Please see the help screen for my details::

  $ lptimesheet -h


Author
------

Malthe Borch <mborch@gmail.com>


License
-------

BSD. Use at own risk.
