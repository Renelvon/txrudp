Change Log
==========

All notable changes to this project will be documented in this file.
This project adheres to `Semantic Versioning <http://semver.org/>`__.

[0.2.0] - 2015-06-25
--------------------

Added
~~~~~
-  More thorough unit tests.
-  Simple benchmarks / functional tests.

Changed
~~~~~~~
-  Switched to a 3-state model for simplicity. The ``INITIAL`` state was merged with ``CONNECTING`` and the ``HALF-CONNECTED`` state was merged with ``CONNECTED``.
-  Slightly lowered the ``PACKET_TIMEOUT``; significantly lowered ``BARE_ACK_TIMEOUT``, it is almost instantaneous.

Fixed
~~~~~
-  No longer processing duplicate packets.
-  Handler no longer receives out-of-order messages if packets are missed.

[0.1.0] - 2015-06-21
--------------------

Added
~~~~~
-  Created a changelog to document changes.
