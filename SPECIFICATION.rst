General
=======

``txrudp`` is an extension of the ``Twisted`` framework that enables virtual connections over classic UDP sockets, aka *Reliable UDP*. It is ideal for message-oriented architectures where in-order delivery is required. This document serves as a mini-specification of the protocol used.

Packet structure
----------------
An *RUDP packet* is a Python object that can be serialized and deserialized using the protobuf spec described in ``txrudp/packet.proto`` and repeated here for reference. Conformant implementations of the ``txrudp`` protocol MUST reject (silently or not) any packet that violates the said spec. During transmission, the packet SHOULD be encoded using protobuf. Ports and IP fields SHOULD conform to standard requirements. IPv6 addreses are allowed.

::

    syntax = "proto2";

    package txrudp;

    option optimize_for = LITE_RUNTIME;

    message Packet {
        optional bool syn = 1;
        optional bool fin = 2;

        optional uint64 sequence_number = 3;
        optional uint64 more_fragments = 4;
        optional uint64 ack = 5;

        optional bytes payload = 6;

        required string dest_ip = 7;
        required uint32 dest_port = 8;

        required string source_ip = 9;
        required uint32 source_port = 10;
    }

::

Packet types and conventions
----------------------------
A valid RUDP packet may fall in one of the following categories:

SYN
    The ``syn`` field MUST be ``True``, the ``fin`` field MUST be ``False``, the ``sequence_number`` field MUST be positive. The ``ack`` field MAY be positive. The ``payload`` field MAY be non-empty, but SHOULD not contain a message to be delivered; it MAY contain information needed to set up a specific sort of connection (e.g. keypairs, timestamps, e.t.c).
ACK
    The ``syn`` field MUST be ``False``, the ``fin`` field MUST be ``False``, the ``sequence_number`` field MUST be ``0``, the ``ack`` field MUST be positive and the ``payload`` field MUST be empty. This type of packet is also called 'bare' or 'standalone' ACK packet.
FIN
    The ``syn`` field MUST be ``False``, the ``fin`` field MUST be ``True``, the ``sequence_number`` field MUST be ``0`` and the ``payload`` field MUST be empty. The ``ack`` field MAY be positive.
casual
    The ``syn`` field MUST be ``False``, the ``fin`` field MUST be ``False``, the ``sequence_number`` field MUST be positive and the ``payload`` field MUST be non-empty. The ``ack`` field MAY be positive.

Sequence numbers and acknowledgement
------------------------------------
Every SYN and casual packet has its unique sequence number which is not repeated until the end of the communication. At the start of the communication, the two endpoints announce to each other the sequence numbers they will use by sending a SYN packet with the initial sequence number. Sending an ACK or a casual packet with acknowledgement number ``N`` is treated as an acknowledgement of correct reception of all packets with sequence number *less* than ``N``.

Connection states
-----------------
There are in total 3 possible states for an RUDP connection:

CONNECTING
    The local endpoint has just woken up and is attempting to establish connection with the remote one; it is sending SYN packets with its chosen sequence number to the remote endpoint and is expecting SYN packets as a reply. It will refuse to receive casual or ACK packets; it will cache outbound messages to send them later. The endpoint can be shutdown either directly or by receiving a FIN packet; if such an event happens, it will move to the SHUTDOWN state. The endpoint can be set to CONNECTED by receiving a SYN packet with a proper (i.e. positive) sequence number from the remote endpoint.

CONNECTED
    The remote endpoint has successfully established connection with the local one, and so casual packets can be send and received. Any SYN packets receiving after transitioning to ``CONNECTED`` are silently dropped. The endpoint can be shutdown either directly or by receiving a FIN packet; if such an event happens, it will move to the SHUTDOWN state. The local endpoint can receive ACK packets and may also send of its own.

SHUTDOWN
    The remote endpoint appears to be no longer accessible or not responding or the protocol has been broken in some other way. The local endpoint is no longer sending messages or processing received messages. The connection cannot be reestablished until both endpoints garbage-collect the current ``Connection`` objects and create new ones. A node may refuse to do so, if it believes that the remote endpoint is not worth communicating with; in such a case, the shutdown connection will silently siphon all incoming messages.

Cryptographic support
---------------------
There is built-in support for confidential communications, provided by ``CryptoConnection`` and ``CryptoConnectionFactory``, using the well-known ``NaCl`` library. Here is a list of operational differences when using ``CryptoConnection``:

- Each connection is optionally instantiated with a hex-encoded private ECC key suitable for use with the ``NaCl`` library. See the documentation of the ``PyNaCl`` package for further details. If such a private key is not given during instatiation, it is generated on the spot.

- All SYN messages carry a payload: a byte-encoded public key suitable for use with the ``NaCl`` library. This public key should correspond to the private key the sender of the SYN message holds.

- The payloads of all non-SYN messages are encrypted/decrypted using the ``Box`` constructed from the remote endpoint's public key and the local private key. This applies to ACK and FIN, as well, despite their payloads being empty, for reasons of sender authentication.

**WARNING**: The user of a ``CryptoConnection`` class is responsible to validate the authenticity of a received public key. Failure to do so may lead to MitM attacks. Users of relayed connections should be especially vigilant.
