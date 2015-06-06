import collections
import json
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

    def _make_cm_with_mocks(self):
        cf = mock.Mock(spec_set=connection.RUDPConnectionFactory)
        return rudp.ConnectionMultiplexer(cf, self.public_ip)

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
            relaying=True
        )
        self.assertEqual(cm.public_ip, self.public_ip)
        self.assertTrue(cm.relaying)

    def test_make_connection(self):
        transport = proto_helpers.StringTransportWithDisconnection()
        cm = self._make_cm_with_mocks()
        cm.makeConnection(transport)
        self.assertIs(cm.transport, transport)

    def test_get_nonexistent_connection(self):
        cm = self._make_cm_with_mocks()
        self.assertNotIn(self.addr1, cm)
        with self.assertRaises(KeyError):
            con = cm[self.addr1]
        
    def test_set_and_get_new_connection(self):
        cm = self._make_cm_with_mocks()
        mock_connection = mock.Mock(spec_set=connection.RUDPConnection)
        cm[self.addr1] = mock_connection
        self.assertIn(self.addr1, cm)
        self.assertIs(cm[self.addr1], mock_connection)

    def test_set_existent_connection(self):
        cm = self._make_cm_with_mocks()
        mock_connection1 = mock.Mock(spec_set=connection.RUDPConnection)
        mock_connection2 = mock.Mock(spec_set=connection.RUDPConnection)
        cm[self.addr1] = mock_connection1
        cm[self.addr1] = mock_connection2
        self.assertIn(self.addr1, cm)
        self.assertIs(cm[self.addr1], mock_connection2)
        mock_connection1.shutdown.assert_called_once_with()
        mock_connection2.shutdown.assert_not_called()

    def test_del_nonexistent_connection(self):
        cm = self._make_cm_with_mocks()
        self.assertNotIn(self.addr1, cm)
        with self.assertRaises(KeyError):
            del cm[self.addr1]

    def test_del_existent_connection(self):
        cm = self._make_cm_with_mocks()
        mock_connection = mock.Mock(spec_set=connection.RUDPConnection)
        cm[self.addr1] = mock_connection
        del cm[self.addr1]
        self.assertNotIn(self.addr1, cm)

    def test_iter(self):
        cm = self._make_cm_with_mocks()
        mock_connection1 = mock.Mock(spec_set=connection.RUDPConnection)
        mock_connection2 = mock.Mock(spec_set=connection.RUDPConnection)
        cm[self.addr1] = mock_connection1
        cm[self.addr2] = mock_connection2
        self.assertItemsEqual(iter(cm), (self.addr1, self.addr2))

    def test_send_datagram(self):
        transport = mock.Mock()
        cm = self._make_cm_with_mocks()
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
        cm = self._make_cm_with_mocks()
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
