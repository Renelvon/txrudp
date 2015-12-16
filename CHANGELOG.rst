Change Log
==========

All notable changes to this project will be documented in this file.
This project adheres to `Semantic Versioning <http://semver.org/>`__.


[0.4.2] - 2015-12-16
--------------------

Added
~~~~~
-  Add IP banning methods in the ConnectionMultiplexer class.

[0.4.1] - 2015-11-05
--------------------

Changed
~~~~~~~
-  Check that an incoming packet is a SYN packet before creating a new connection. Prevents a connect/disconnect
   loop in some error cases.

[0.4.0] - 2015-07-14
--------------------

Added
~~~~~
-  Add an optional encryption layer that uses ``pynacl`` to deliver baseline confidentiality.
   To take advantage of the new feature, just use ``Crypto-`` classes instead of the casual ones.
   The cryptographic keys generated are meant to be used only during a single connection, for
   forward secrecy. However, one can also force usage of a specific private key; see the constructor
   of ``CryptoConnection`` for more details.

Changed
~~~~~~~
-  Support for OSes other than Linux is currently limited because of ``pynacl``'s restricted availability.
-  Update and clarify specification of sequence numbers.

Fixed
~~~~~
-  Minor fixes affecting docstrings and memory usage.
-  Improved packaging.

[0.3.0] - 2015-07-06
--------------------

Added
~~~~~
-  Add protobuf specification and skeleton class.
-  ``Connection`` now has an ``unregister`` method that simplifies detaching
   the instance from the protocol. Note: The said method is *not* automatically
   invoked on connection shutdown.

Changed
~~~~~~~
-  Replace JSON (de)serialization with protobuf (de)serialization; reap substantial speed boost.
-  Support for Python 3 is dropped until protobuf supports it too.
-  packet.Packet constructor signature is no longer suitable for obtaining instances;
   use the new factory methods (``from_bytes``, ``from_data``).

Fixed
~~~~~
-  Corrected typos in dependency specification.

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
