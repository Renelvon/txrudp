import collections

import mock
from twisted.internet import reactor, task
from twisted.trial import unittest

from txrudp import connection, packet, rudp


class TestScheduledPacketAPI(unittest.TestCase):

    """Test API (attributes) of ScheduledPacket subclass."""

    @classmethod
    def setUpClass(cls):
        cls.spclass = connection.RUDPConnection.ScheduledPacket

    def test_default_init(self):
        rudp_packet = packet.RUDPPacket(
            1,
            '123.45.67.89',
            12345,
            '213.54.76.98',
            54321
        )
        timeout = 0.7
        timeout_cb = reactor.callLater(timeout, lambda: None)
        sp = self.spclass(rudp_packet, timeout, timeout_cb)

        self.assertEqual(sp.rudp_packet, rudp_packet)
        self.assertEqual(sp.timeout, timeout)
        self.assertEqual(sp.timeout_cb, timeout_cb)
        self.assertEqual(sp.retries, 0)

        timeout_cb.cancel()


    def test_init_with_retries(self):
        rudp_packet = packet.RUDPPacket(
            1,
            '123.45.67.89',
            12345,
            '213.54.76.98',
            54321
        )
        timeout = 0.7
        timeout_cb = reactor.callLater(timeout, lambda: None)
        sp = self.spclass(rudp_packet, timeout, timeout_cb, retries=10)

        self.assertEqual(sp.rudp_packet, rudp_packet)
        self.assertEqual(sp.timeout, timeout)
        self.assertEqual(sp.timeout_cb, timeout_cb)
        self.assertEqual(sp.retries, 10)

        timeout_cb.cancel()


class TestRUDPConnectionAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.clock = task.Clock()
        connection.REACTOR.callLater = cls.clock.callLater

        cls.public_ip = '123.45.67.89'
        cls.port = 12345
        cls.own_addr = (cls.public_ip, cls.port)
        cls.addr1 = ('132.54.76.98', 54321)
        cls.addr2 = ('231.76.45.89', 15243)

    def setUp(self):
        self.proto_mock = mock.Mock(spec_set=rudp.ConnectionMultiplexer)
        self.handler_mock = mock.Mock(spec_set=connection.Handler)

    def test_default_init(self):
        con = connection.RUDPConnection(
            self.proto_mock,
            self.handler_mock,
            self.own_addr,
            self.addr1
        )

        self.assertEqual(con.handler, self.handler_mock)
        self.assertEqual(con.own_addr, self.own_addr)
        self.assertEqual(con.dest_addr, self.addr1)
        self.assertEqual(con.relay_addr, self.addr1)
        self.assertFalse(con.connected)

        self.clock.advance(0)
        self.addCleanup(con.shutdown)

    def test_init_with_relay(self):
        con = connection.RUDPConnection(
            self.proto_mock,
            self.handler_mock,
            self.own_addr,
            self.addr1,
            self.addr2
        )

        self.assertEqual(con.handler, self.handler_mock)
        self.assertEqual(con.own_addr, self.own_addr)
        self.assertEqual(con.dest_addr, self.addr1)
        self.assertEqual(con.relay_addr, self.addr2)
        self.assertFalse(con.connected)

        self.clock.advance(0)
        self.addCleanup(con.shutdown)
