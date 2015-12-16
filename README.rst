txrudp
======

|Build Status| |Code Health| |Coverage Status| |PyPI Status|

Implementation of a Reliable UDP Protocol Layer over Twisted.

This implementation makes no explicit effort to adhere to any published
standard about RUDP (RFCs, etc).

Installation
------------
::

    pip install txrudp

In order to use encrypted connections, you need to install ``txrudp`` with
the ``crypto`` extension:

::

    pip install txrudp[crypto]

This extension denends on the ``PyNaCl`` package, and attempts to install it
as part of the setup. Installation is known to fail on Windows. See
`this <http://geroyblog.blogspot.gr/2015/03/compiling-and-using-pynacl-on-windows-7.html>`__
about manually installing ``PyNaCl`` on Windows.

Python 3 support
----------------
Support for Python 3 will be made available as soon as the ``protobuf`` package officially
supports Python 3.

Resources
---------
-  `Original node.js library <https://github.com/shovon/node-rudp>`__
-  `Original port to Python <https://github.com/hoffmabc/python-rudp>`__
-  `PyNaCl <https://pynacl.readthedocs.org/en/latest/public/>`__
-  `Protobuf <https://developers.google.com/protocol-buffers/>`__

License
-------

txrudp is released under the `MIT License <LICENSE>`__.

.. |Build Status| image:: https://travis-ci.org/OpenBazaar/txrudp.svg?branch=master
   :target: https://travis-ci.org/OpenBazaar/txrudp
.. |Code Health| image:: https://landscape.io/github/Renelvon/txrudp/master/landscape.svg?style=flat
   :target: https://landscape.io/github/OpenBazaar/txrudp/master
.. |Coverage Status| image:: https://coveralls.io/repos/OpenBazaar/txrudp/badge.svg?branch=master&service=github
   :target: https://coveralls.io/github/OpenBazaar/txrudp?branch=master
.. |PyPI Status| image:: https://badge.fury.io/py/txrudp.svg
   :target: http://badge.fury.io/py/txrudp
   :alt: Latest PyPI version
