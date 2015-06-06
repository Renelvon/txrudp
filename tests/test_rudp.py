import collections
import json
import logging
import unittest

import mock
from twisted.internet import protocol
from twisted.test import proto_helpers

from txrudp import connection, heap, packet, rudp


class TestConnectionManagerAPI(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.public_ip = '123.45.67.89'
        cls.port = 12345
        cls.addr1 = (cls.public_ip, cls.port)
        cls.addr2 = (cls.public_ip, cls.port + 1)
        cls.addr3 = (cls.public_ip, cls.port + 2)

    def _make_cm(self):
        cf = mock.Mock(spec_set=connection.RUDPConnectionFactory)
        return rudp.ConnectionMultiplexer(
            cf,
            self.public_ip,
            logger=logging.Logger('CM')
        )

    def test_default_init(self):
        cf = mock.Mock()
        cm = rudp.ConnectionMultiplexer(cf, self.public_ip)
        self.assertIsInstance(cm, protocol.DatagramProtocol)
        self.assertIsInstance(cm, collections.MutableMapping)
        self.assertEqual(cm.public_ip, self.public_ip)
        self.assertFalse(cm.relaying)
        self.assertEqual(len(cm), 0)

    def test_full_init(self):
        cf = mock.Mock()
        cm = rudp.ConnectionMultiplexer(
            connection_factory=cf,
            public_ip=self.public_ip,
            relaying=True,
            logger=logging.Logger('CM')
        )
        self.assertEqual(cm.public_ip, self.public_ip)
        self.assertTrue(cm.relaying)

    def test_make_connection(self):
        transport = proto_helpers.StringTransportWithDisconnection()
        cm = self._make_cm()
        cm.makeConnection(transport)
        self.assertIs(cm.transport, transport)

    def test_get_nonexistent_connection(self):
        cm = self._make_cm()
        self.assertNotIn(self.addr1, cm)
        with self.assertRaises(KeyError):
            con = cm[self.addr1]
        
    def test_set_and_get_new_connection(self):
        cm = self._make_cm()
        mock_connection = mock.Mock(spec_set=connection.RUDPConnection)
        cm[self.addr1] = mock_connection
        self.assertIn(self.addr1, cm)
        self.assertIs(cm[self.addr1], mock_connection)

    def test_set_existent_connection(self):
        cm = self._make_cm()
        mock_connection1 = mock.Mock(spec_set=connection.RUDPConnection)
        mock_connection2 = mock.Mock(spec_set=connection.RUDPConnection)
        cm[self.addr1] = mock_connection1
        cm[self.addr1] = mock_connection2
        self.assertIn(self.addr1, cm)
        self.assertIs(cm[self.addr1], mock_connection2)
        mock_connection1.shutdown.assert_called_once_with()
        mock_connection2.shutdown.assert_not_called()

    def test_del_nonexistent_connection(self):
        cm = self._make_cm()
        self.assertNotIn(self.addr1, cm)
        with self.assertRaises(KeyError):
            del cm[self.addr1]

    def test_del_existent_connection(self):
        cm = self._make_cm()
        mock_connection = mock.Mock(spec_set=connection.RUDPConnection)
        cm[self.addr1] = mock_connection
        del cm[self.addr1]
        self.assertNotIn(self.addr1, cm)

    def test_iter(self):
        cm = self._make_cm()
        mock_connection1 = mock.Mock(spec_set=connection.RUDPConnection)
        mock_connection2 = mock.Mock(spec_set=connection.RUDPConnection)
        cm[self.addr1] = mock_connection1
        cm[self.addr2] = mock_connection2
        self.assertItemsEqual(iter(cm), (self.addr1, self.addr2))

    def test_receive_bad_json_datagram(self):
        cm = self._make_cm()
        mock_connection = mock.Mock(spec_set=connection.RUDPConnection)
        cm[self.addr1] = mock_connection
        datagram = '!@#4noise%^&*'
        cm.datagramReceived(datagram, self.addr1)
        mock_connection.receive_packet.assert_not_called()

    def test_receive_bad_rudp_datagram(self):
        cm = self._make_cm()
        mock_connection = mock.Mock(spec_set=connection.RUDPConnection)
        cm[self.addr1] = mock_connection
        datagram = json.dumps(
            packet.RUDPPacket(
                -1,  # Bad sequence number
                '123.45.67.89',
                12345,
                '132.54.76.98',
                54321
            ).to_json()
        )
        cm.datagramReceived(datagram, self.addr1)
        mock_connection.receive_packet.assert_not_called()

    def test_receive_relayed_datagram_but_not_relaying(self):
        cm = self._make_cm()
        transport = mock.Mock()
        cm.makeConnection(transport)

        dest_ip = '231.54.67.89'  # not the same as self.public_ip
        source_addr = self.addr1
        datagram = json.dumps(
            packet.RUDPPacket(
                1,
                dest_ip,
                12345,
                source_addr[0],
                source_addr[1]
            ).to_json()
        )

        cm.datagramReceived(datagram, source_addr)
        self.assertNotIn(dest_ip, cm)
        transport.write.assert_not_called()
        cm.connection_factory.make_new_connection.assert_not_called()

    def test_receive_relayed_datagram_while_relaying(self):
        cm = self._make_cm()
        transport = mock.Mock()
        cm.makeConnection(transport)
        cm.relaying = True

        dest_ip = '231.54.67.89'  # not the same as self.public_ip
        source_addr = self.addr1
        datagram = json.dumps(
            packet.RUDPPacket(
                1,
                dest_ip,
                12345,
                source_addr[0],
                source_addr[1]
            ).to_json()
        )

        cm.datagramReceived(datagram, source_addr)
        self.assertNotIn(dest_ip, cm)
        transport.write.assert_called_once_with(datagram, (dest_ip, 12345))
        cm.connection_factory.make_new_connection.assert_not_called()

    def test_make_new_connection(self):
        cm = self._make_cm()
        con = cm.make_new_connection(self.addr1, self.addr2)
        self.assertIn(self.addr2, cm)
        cm.connection_factory.make_new_connection.assert_called_once_with(
            cm,
            self.addr1,
            self.addr2,
            None
        )

    def test_make_new_relaying_connection(self):
        cm = self._make_cm()
        con = cm.make_new_connection(self.addr1, self.addr2, self.addr3)
        self.assertIn(self.addr2, cm)
        cm.connection_factory.make_new_connection.assert_called_once_with(
            cm,
            self.addr1,
            self.addr2,
            self.addr3
        )

    def test_send_datagram(self):
        transport = mock.Mock()
        cm = self._make_cm()
        cm.makeConnection(transport)
        rudp_packet = packet.RUDPPacket(
            1,
            '132.54.76.98',
            23456,
            self.public_ip,
            self.port
        )
        datagram = json.dumps(rudp_packet.to_json())

        cm.send_datagram(datagram, ('132.54.76.98', 23456))
        transport.write.assert_called_once_with(
            datagram,
            ('132.54.76.98', 23456)
        )

    def test_shutdown(self):
        cm = self._make_cm()
        mock_connection1 = mock.Mock(spec_set=connection.RUDPConnection)
        mock_connection2 = mock.Mock(spec_set=connection.RUDPConnection)
        cm[self.addr1] = mock_connection1
        cm[self.addr2] = mock_connection2

        transport = mock.Mock()
        cm.makeConnection(transport)

        cm.shutdown()
        mock_connection1.shutdown.assert_called_once_with()
        mock_connection2.shutdown.assert_called_once_with()
        transport.loseConnection.assert_called_once_with()
