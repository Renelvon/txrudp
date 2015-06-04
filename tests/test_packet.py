import unittest

from txrudp import packet


class TestPacketAPI(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.dest_ip, cls.dest_port = '123.45.67.89', 12345
        cls.source_ip, cls.source_port = '132.45.67.89', 54321

    def test_init_with_minimal_parametres(self):
        p = packet.RUDPPacket(
            1,
            self.dest_ip,
            self.dest_port,
            self.source_ip,
            self.source_port,
        )
        self.assertEqual(p.sequence_number, 1)
        self.assertEqual(p.dest_ip, self.dest_ip)
        self.assertEqual(p.dest_port, self.dest_port)
        self.assertEqual(p.source_ip, self.source_ip)
        self.assertEqual(p.source_port, self.source_port)
        self.assertEqual(p.payload, '')
        self.assertEqual(p.more_fragments, 0)
        self.assertEqual(p.ack, 0)
        self.assertFalse(p.fin)
        self.assertFalse(p.syn)

    def test_init_with_all_parametres(self):
        p = packet.RUDPPacket(
            sequence_number=1,
            dest_ip=self.dest_ip,
            dest_port=self.dest_port,
            source_ip=self.source_ip,
            source_port=self.source_port,
            payload='Yellow submarine',
            more_fragments=4,
            ack=28,
            fin=True,
            syn=True
        )
        self.assertEqual(p.sequence_number, 1)
        self.assertEqual(p.dest_ip, self.dest_ip)
        self.assertEqual(p.dest_port, self.dest_port)
        self.assertEqual(p.source_ip, self.source_ip)
        self.assertEqual(p.source_port, self.source_port)
        self.assertEqual(p.payload, 'Yellow submarine')
        self.assertEqual(p.more_fragments, 4)
        self.assertEqual(p.ack, 28)
        self.assertTrue(p.fin)
        self.assertTrue(p.syn)

    def _make_packet_with_seqnum(self, seqnum):
        return packet.RUDPPacket(
            seqnum,
            self.dest_ip,
            self.dest_port,
            self.source_ip,
            self.source_port,
        )

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

    def test_to_json(self):
        p = packet.RUDPPacket(
            sequence_number=1,
            dest_ip=self.dest_ip,
            dest_port=self.dest_port,
            source_ip=self.source_ip,
            source_port=self.source_port,
            payload='Yellow submarine',
            more_fragments=4,
            ack=28,
            fin=True,
            syn=True
        )
        json_dict = {
            'sequence_number': 1,
            'dest_ip': self.dest_ip,
            'dest_port': self.dest_port,
            'source_ip': self.source_ip,
            'source_port': self.source_port,
            'payload': 'Yellow submarine',
            'more_fragments': 4,
            'ack': 28,
            'fin': True,
            'syn': True
        }
        self.assertEqual(p.to_json(), json_dict)

    def test_from_validated_json(self):
        json_dict = {
            'sequence_number': 1,
            'dest_ip': self.dest_ip,
            'dest_port': self.dest_port,
            'source_ip': self.source_ip,
            'source_port': self.source_port,
            'payload': 'Yellow submarine',
            'more_fragments': 4,
            'ack': 28,
            'fin': True,
            'syn': True
        }
        p = packet.RUDPPacket.from_validated_json(json_dict)
        self.assertEqual(p.sequence_number, json_dict['sequence_number'])
        self.assertEqual(p.dest_ip, json_dict['dest_ip'])
        self.assertEqual(p.dest_port, json_dict['dest_port'])
        self.assertEqual(p.source_ip, json_dict['source_ip'])
        self.assertEqual(p.source_port, json_dict['source_port'])
        self.assertEqual(p.payload, json_dict['payload'])
        self.assertEqual(p.more_fragments, json_dict['more_fragments'])
        self.assertEqual(p.ack, json_dict['ack'])
        self.assertEqual(p.fin, json_dict['fin'])
        self.assertEqual(p.syn, json_dict['syn'])
