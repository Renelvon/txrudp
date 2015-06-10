"""
Specification of RUDP packet structure.

Classes:
    RUDPPacket: An RUDP packet implementing a total ordering
        and serializing to/from JSON.
"""

import functools

import jsonschema

# NOTE: jsonschema's `format` specifier was tested and found
# lacking. Hence the use of regexes from Regular Expressions Cookbook.
# For now, only standard (non-compressed) IPv6 addresses are
# supported. This might change in the future.
_IPV4_REGEX = '^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
_IPV6_REGEX = '^(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}$'

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


@functools.total_ordering
class RUDPPacket(object):

    """An RUDP packet."""

    def __init__(
        self,
        sequence_number,
        dest_addr,
        source_addr,
        payload='',
        more_fragments=0,
        ack=0,
        fin=False,
        syn=False,
    ):
        """
        Create a new packet with the given fields.

        Args:
            seqnum: The packet's sequence number, as an int.
            dest_addr: Tuple of destination addres (ip, port).
            source_addr: Tuple of local host addres (ip, port).
            payload: The packet's payload, as a string.
            more_fragments: The number of segments that follow this
                packet and are delivering remaining parts of the same
                payload.
            ack: If positive, it is the acknowledgement number of
                the next packet the receiver is expecting. Otherwise,
                ignore.
            fin: When True, signals that this packet ends the connection.
            syn: When True, signals the start of a new conenction.

        NOTE: The destination address may not be the address of the
        first recipient of this packet in case where the recipient is
        a mediator node relaying packet (e.g. for NAT punching).
        """
        self.sequence_number = sequence_number
        self.dest_addr = dest_addr
        self.source_addr = source_addr
        self.payload = payload
        self.more_fragments = more_fragments
        self.ack = ack
        self.fin = fin
        self.syn = syn

    def __eq__(self, other):
        if isinstance(other, RUDPPacket):
            return self.sequence_number == other.sequence_number
        else:
            return NotImplemented

    def __lt__(self, other):
        if isinstance(other, RUDPPacket):
            return self.sequence_number < other.sequence_number
        else:
            return NotImplemented

    def to_json(self):
        """
        Create a JSON object representing this packet.

        Returns:
            A JSON object that should be valid against
            RUDP_PACKET_JSON_SCHEMA.
        """
        return {
            'sequence_number': self.sequence_number,
            'dest_ip': self.dest_addr[0],
            'dest_port': self.dest_addr[1],
            'source_ip': self.source_addr[0],
            'source_port': self.source_addr[1],
            'payload': self.payload,
            'more_fragments': self.more_fragments,
            'ack': self.ack,
            'fin': self.fin,
            'syn': self.syn
        }

    @classmethod
    def from_unvalidated_json(cls, json_obj):
        """
        Create an RUDPPacket from an unvalidated json_obj.

        Args:
            json_obj: An RUDP packet in JSON format.

        Returns:
            An RUDPMesssage instance representing the same packet.

        Raises:
            jsonschema.ValidationError: The packet was invalid.
        """
        cls.validate(json_obj)
        return cls.from_validated_json(json_obj)

    @classmethod
    def from_validated_json(cls, json_obj):
        """
        Create an RUDPPacket from a validated json_obj.

        Args:
            json_obj: An RUDP packet in JSON format.

        Returns:
            An RUDPMesssage instance representing the same packet.
        """
        sequence_number = int(json_obj['sequence_number'])
        dest_addr = (json_obj['dest_ip'], int(json_obj['dest_port']))
        source_addr = (json_obj['source_ip'], int(json_obj['source_port']))
        payload = json_obj['payload']
        more_fragments = json_obj['more_fragments']
        ack = int(json_obj['ack'])
        fin = bool(json_obj['fin'])
        syn = bool(json_obj['syn'])

        return cls(
            sequence_number,
            dest_addr,
            source_addr,
            payload,
            more_fragments,
            ack,
            fin,
            syn
        )

    @staticmethod
    def validate(packet):
        """
        Test the packet against RUDP_PACKET_JSON_SCHEMA.

        Args:
            packet: The packet to validate, as a JSON object.

        Raises:
            jsonschema.ValidationError: The packet was invalid.
        """
        jsonschema.validate(packet, RUDP_PACKET_JSON_SCHEMA)
