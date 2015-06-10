import collections
import json

import mock
from twisted.internet import reactor, task
from twisted.trial import unittest

from txrudp import connection, constants, packet, rudp


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

    def test_syn_repeat(self):
        con = connection.RUDPConnection(
            self.proto_mock,
            self.handler_mock,
            self.own_addr,
            self.addr1
        )

        for _ in range(constants.MAX_RETRANSMISSIONS):
            # Each advance forces a SYN packet retransmission.
            self.clock.advance(constants.PACKET_TIMEOUT)

        # Force transmission of FIN packet and shutdown.
        self.clock.advance(constants.PACKET_TIMEOUT)

        # Trap any calls after shutdown.
        self.clock.advance(100 * constants.PACKET_TIMEOUT)
        connection.REACTOR.runUntilCurrent()

        m_calls = self.proto_mock.send_datagram.call_args_list
        self.assertEqual(len(m_calls), constants.MAX_RETRANSMISSIONS + 1)

        first_syn_call = m_calls[0]
        syn_packet = json.loads(first_syn_call[0][0])
        address = first_syn_call[0][1]

        self.assertEqual(address, con.relay_addr)
        self.assertGreater(syn_packet['sequence_number'], 0)
        self.assertLess(syn_packet['sequence_number'], 2**16)

        expected_syn_packet = packet.RUDPPacket(
            syn_packet['sequence_number'],
            con.dest_addr[0],
            con.dest_addr[1],
            con.own_addr[0],
            con.own_addr[1],
            syn=True
        ).to_json()

        for call in m_calls[:-1]:
            self.assertEqual(json.loads(call[0][0]), expected_syn_packet)
            self.assertEqual(call[0][1], address)

        expected_fin_packet = packet.RUDPPacket(
            0,
            con.dest_addr[0],
            con.dest_addr[1],
            con.own_addr[0],
            con.own_addr[1],
            fin=True
        ).to_json()

        self.assertEqual(json.loads(m_calls[-1][0][0]), expected_fin_packet)
        self.assertEqual(m_calls[-1][0][1], address)
        self.addCleanup(con.shutdown)
