General
=======

``txrudp`` is an extension of the ``Twisted`` framework that enables virtual connections over classic UDP sockets, aka *Reliable UDP*. It is ideal for message-oriented architectures where in-order delivery is required. This document serves as a mini-specification of the protocol used.

Packet structure
----------------
An *RUDP packet* is a JSON object that follows the schema described in the ``txrudp/packet.py`` and repeated here for reference. Conformant implementations of the ``txrudp`` protocol MUST reject (silently or not) any packet that violates the said schema. During transmission, the JSON packet SHOULD be encoded as a string; the order of the fields does not matter, so long the receiver can successfully decode the packet using a JSON decoder; the builtin decoder inside Python's ``json`` package SHOULD be able to decode the packet successfully.

::

    _IPV4_REGEX = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'

    # For now, only standard (non-compressed) IPv6 addresses are
    # supported. This might change in the future.
    _IPV6_REGEX = r'^(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}$'

    RUDP_PACKET_JSON_SCHEMA = {
        '$schema': 'http://json-schema.org/schema#',
        'id': 'RUDP_PACKET_JSON_SCHEMA',
        'type': 'object',
        'properties': {
            'sequence_number': {
                'type': 'integer',
                'minimum': 0
            },
            'dest_ip': {
                'anyOf': [
                    {'type': 'string', 'pattern': _IPV4_REGEX},
                    {'type': 'string', 'pattern': _IPV6_REGEX}
                ]
            },
            'dest_port': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 65535
            },
            'source_ip': {
                'anyOf': [
                    {'type': 'string', 'pattern': _IPV4_REGEX},
                    {'type': 'string', 'pattern': _IPV6_REGEX}
                ]
            },
            'source_port': {
                'type': 'integer',
                'minimum': 1,
                'maximum': 65535
            },
            'payload': {
                'type': 'string',
                'default': ''
            },
            'more_fragments': {
                'type': 'integer',
                'minimum': 0,
                'default': 0
            },
            'ack': {
                'type': 'integer',
                'minimum': 0,
                'default': 0
            },
            'fin': {
                'type': 'boolean',
                'default': False
            },
            'syn': {
                'type': 'boolean',
                'default': False
            },
        },
        'additionalProperties': False,
        'required': [
            'sequence_number',
            'dest_ip',
            'dest_port',
            'source_ip',
            'source_port',
            'payload',
            'ack',
            'fin',
            'syn',
            'more_fragments'
        ],
    }

::

Packet types and conventions
----------------------------
A valid RUDP packet may fall in one of the following categories:

SYN
    The ``syn`` field MUST be ``True``, the ``fin`` field MUST be ``False``. The ``ack`` field MAY be positive. The ``payload`` field MAY be non-empty, but SHOULD not contain a message to be delivered; it MAY contain information needed to set up a specific sort of connection (e.g. keypairs, timestamps, e.t.c).
ACK
    The ``syn`` field MUST be ``False``, the ``fin`` field MUST be ``False``, the ``ack`` field MUST be positive and the ``payload`` field MUST be empty. This type of packet is also called 'bare' or 'standalone' ACK packet.
FIN
    The ``syn`` field MUST be ``False``, the ``fin`` field MUST be ``True`` and the ``payload`` field MUST be empty. The ``ack`` field MAY be positive.
casual
    The ``syn`` field MUST be ``False``, the ``fin`` field MUST be ``False`` and the ``payload`` field MUST be non-empty. The ``ack`` field MAY be positive.

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
