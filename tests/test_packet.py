import unittest

import jsonschema

from txrudp import packet


class TestPacketAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dest_addr = ('123.45.67.89', 12345)
        cls.source_addr = ('132.45.67.89', 54321)
        cls.json_dict = {
            'sequence_number': 1,
            'dest_ip': cls.dest_addr[0],
            'dest_port': cls.dest_addr[1],
            'source_ip': cls.source_addr[0],
            'source_port': cls.source_addr[1],
            'payload': 'Yellow submarine',
            'more_fragments': 4,
            'ack': 28,
            'fin': True,
            'syn': True
        }

    def test_init_with_minimal_parametres(self):
        p = packet.RUDPPacket(1, self.dest_addr, self.source_addr)
        self.assertEqual(p.sequence_number, 1)
        self.assertEqual(p.dest_addr, self.dest_addr)
        self.assertEqual(p.source_addr, self.source_addr)
        self.assertEqual(p.payload, '')
        self.assertEqual(p.more_fragments, 0)
        self.assertEqual(p.ack, 0)
        self.assertFalse(p.fin)
        self.assertFalse(p.syn)

    def test_init_with_all_parametres(self):
        p = packet.RUDPPacket(
            sequence_number=1,
            dest_addr=self.dest_addr,
            source_addr=self.source_addr,
            payload='Yellow submarine',
            more_fragments=4,
            ack=28,
            fin=True,
            syn=True
        )
        self.assertEqual(p.sequence_number, 1)
        self.assertEqual(p.dest_addr, self.dest_addr)
        self.assertEqual(p.source_addr, self.source_addr)
        self.assertEqual(p.payload, 'Yellow submarine')
        self.assertEqual(p.more_fragments, 4)
        self.assertEqual(p.ack, 28)
        self.assertTrue(p.fin)
        self.assertTrue(p.syn)

    def _make_packet_with_seqnum(self, seqnum):
        return packet.RUDPPacket(seqnum, self.dest_addr, self.source_addr)

    def test_ordering(self):
        p1 = self._make_packet_with_seqnum(1)
        p2 = self._make_packet_with_seqnum(2)
        p3 = self._make_packet_with_seqnum(1)

        self.assertEqual(p1, p1)
        self.assertNotEqual(p1, p2)
        self.assertEqual(p1, p3)

        self.assertGreater(p2, p1)
        self.assertLess(p1, p2)

        self.assertGreaterEqual(p1, p1)
        self.assertLessEqual(p1, p1)

    def _assert_packet_equals_json(self, p, json_obj):
        self.assertEqual(p.sequence_number, json_obj['sequence_number'])
        self.assertEqual(p.dest_addr[0], json_obj['dest_ip'])
        self.assertEqual(p.dest_addr[1], json_obj['dest_port'])
        self.assertEqual(p.source_addr[0], json_obj['source_ip'])
        self.assertEqual(p.source_addr[1], json_obj['source_port'])
        self.assertEqual(p.payload, json_obj['payload'])
        self.assertEqual(p.more_fragments, json_obj['more_fragments'])
        self.assertEqual(p.ack, json_obj['ack'])
        self.assertEqual(p.fin, json_obj['fin'])
        self.assertEqual(p.syn, json_obj['syn'])

    def test_to_json(self):
        p = packet.RUDPPacket(
            sequence_number=1,
            dest_addr=self.dest_addr,
            source_addr=self.source_addr,
            payload='Yellow submarine',
            more_fragments=4,
            ack=28,
            fin=True,
            syn=True
        )
        self.assertEqual(p.to_json(), self.json_dict)

    def test_from_validated_json(self):
        p = packet.RUDPPacket.from_validated_json(self.json_dict)
        self._assert_packet_equals_json(p, self.json_dict)

    def test_from_unvalidated_good_json(self):
        try:
            p = packet.RUDPPacket.from_validated_json(self.json_dict)
        except Exception:
            self.fail('Unpacking valid JSON failed.')
        else:
            self._assert_packet_equals_json(p, self.json_dict)

    def _assert_json_fails_validation(self, json_obj):
        with self.assertRaises(jsonschema.ValidationError):
            packet.RUDPPacket.from_unvalidated_json(json_obj)

    def test_from_validated_bad_json_with_bad_sequence_number(self):
        bad_json = dict(self.json_dict)

        bad_json['sequence_number'] = -1
        self._assert_json_fails_validation(bad_json)

        bad_json['sequence_number'] = 3.4
        self._assert_json_fails_validation(bad_json)

        del bad_json['sequence_number']
        self._assert_json_fails_validation(bad_json)

    def test_from_validated_bad_json_with_bad_dest_ip(self):
        bad_json = dict(self.json_dict)

        bad_json['dest_ip'] = 42
        self._assert_json_fails_validation(bad_json)

        bad_json['dest_ip'] = '127.0'
        self._assert_json_fails_validation(bad_json)

        bad_json['dest_ip'] = 'FE80:0000:0000::z:B3FF:FE1E:8329'
        self._assert_json_fails_validation(bad_json)

        del bad_json['dest_ip']
        self._assert_json_fails_validation(bad_json)

    def test_from_validated_bad_json_with_bad_dest_port(self):
        bad_json = dict(self.json_dict)

        bad_json['dest_port'] = 3.4
        self._assert_json_fails_validation(bad_json)

        bad_json['dest_port'] = 0
        self._assert_json_fails_validation(bad_json)

        bad_json['dest_port'] = 65536
        self._assert_json_fails_validation(bad_json)

        del bad_json['dest_port']
        self._assert_json_fails_validation(bad_json)

    def test_from_validated_bad_json_with_bad_source_ip(self):
        bad_json = dict(self.json_dict)

        bad_json['source_ip'] = 42
        self._assert_json_fails_validation(bad_json)

        bad_json['source_ip'] = '127.0'
        self._assert_json_fails_validation(bad_json)

        bad_json['source_ip'] = 'FE80:0000:0000:z::B3FF:FE1E:8329'
        self._assert_json_fails_validation(bad_json)

        del bad_json['source_ip']
        self._assert_json_fails_validation(bad_json)

    def test_from_validated_bad_json_with_bad_source_port(self):
        bad_json = dict(self.json_dict)

        bad_json['source_port'] = 3.4
        self._assert_json_fails_validation(bad_json)

        bad_json['source_port'] = 0
        self._assert_json_fails_validation(bad_json)

        bad_json['source_port'] = 65536
        self._assert_json_fails_validation(bad_json)

        del bad_json['source_port']
        self._assert_json_fails_validation(bad_json)

    def test_from_validated_bad_json_with_bad_payload(self):
        bad_json = dict(self.json_dict)

        bad_json['payload'] = 42
        self._assert_json_fails_validation(bad_json)

        del bad_json['payload']
        self._assert_json_fails_validation(bad_json)

    def test_from_validated_bad_json_with_bad_more_fragments(self):
        bad_json = dict(self.json_dict)

        bad_json['more_fragments'] = 3.4
        self._assert_json_fails_validation(bad_json)

        bad_json['more_fragments'] = -1
        self._assert_json_fails_validation(bad_json)

        del bad_json['more_fragments']
        self._assert_json_fails_validation(bad_json)

    def test_from_validated_bad_json_with_bad_ack(self):
        bad_json = dict(self.json_dict)

        bad_json['ack'] = 3.4
        self._assert_json_fails_validation(bad_json)

        bad_json['ack'] = -1
        self._assert_json_fails_validation(bad_json)

        del bad_json['ack']
        self._assert_json_fails_validation(bad_json)

    def test_from_validated_bad_json_with_bad_fin(self):
        bad_json = dict(self.json_dict)

        bad_json['fin'] = 42
        self._assert_json_fails_validation(bad_json)

        del bad_json['fin']
        self._assert_json_fails_validation(bad_json)

    def test_from_validated_bad_json_with_bad_syn(self):
        bad_json = dict(self.json_dict)

        bad_json['syn'] = 42
        self._assert_json_fails_validation(bad_json)

        del bad_json['syn']
        self._assert_json_fails_validation(bad_json)
