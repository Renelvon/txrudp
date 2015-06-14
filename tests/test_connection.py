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
            ('123.45.67.89', 12345),
            ('213.54.76.98', 54321)
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
            ('123.45.67.89', 12345),
            ('213.54.76.98', 54321)
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
        cls.public_ip = '123.45.67.89'
        cls.port = 12345
        cls.own_addr = (cls.public_ip, cls.port)
        cls.addr1 = ('132.54.76.98', 54321)
        cls.addr2 = ('231.76.45.89', 15243)

    def setUp(self):
        self.clock = task.Clock()
        connection.REACTOR.callLater = self.clock.callLater

        self.proto_mock = mock.Mock(spec_set=rudp.ConnectionMultiplexer)
        self.handler_mock = mock.Mock(spec_set=connection.Handler)
        self.con = connection.RUDPConnection(
            self.proto_mock,
            self.handler_mock,
            self.own_addr,
            self.addr1
        )

    def tearDown(self):
        self.con.shutdown()

    def test_default_init(self):
        self.assertEqual(self.con.handler, self.handler_mock)
        self.assertEqual(self.con.own_addr, self.own_addr)
        self.assertEqual(self.con.dest_addr, self.addr1)
        self.assertEqual(self.con.relay_addr, self.addr1)
        self.assertFalse(self.con.connected)

        self.clock.advance(0)

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
        con.shutdown()

    # == Test INITIAL state ==

    def test_send_normal_during_initial(self):
        self.con.send_message('Yellow Submarine')
        self.clock.advance(100)
        connection.REACTOR.runUntilCurrent()
        m_calls = self.proto_mock.send_datagram.call_args_list
        self.assertEqual(len(m_calls), 1)
        self.assertEqual(json.loads(m_calls[0][0][0])['payload'], '')

    def test_shutdown_during_initial(self):
        pass

    def test_receive_fin_during_initial(self):
        fin_rudp_packet = packet.RUDPPacket(
            0,
            self.con.own_addr,
            self.con.dest_addr,
            fin=True
        )

        self.con.receive_packet(fin_rudp_packet)
        self.clock.advance(0)
        connection.REACTOR.runUntilCurrent()

        self.handler_mock.handle_shutdown.assert_not_called()

    def test_receive_syn_during_initial(self):
        remote_seqnum = 42
        remote_syn_packet = packet.RUDPPacket(
            remote_seqnum,
            self.con.own_addr,
            self.con.dest_addr,
            syn=True
        )

        self.con.receive_packet(remote_syn_packet)
        self.assertTrue(self.con.connected)
        for _ in range(constants.MAX_RETRANSMISSIONS):
            # Each advance forces a SYNACK packet retransmission.
            self.clock.advance(constants.PACKET_TIMEOUT)

        # Force transmission of FIN packet and shutdown.
        self.clock.advance(constants.PACKET_TIMEOUT)

        # Trap any calls after shutdown.
        self.clock.advance(100 * constants.PACKET_TIMEOUT)
        connection.REACTOR.runUntilCurrent()

        m_calls = self.proto_mock.send_datagram.call_args_list
        self.assertEqual(len(m_calls), constants.MAX_RETRANSMISSIONS + 1)

        first_synack_call = m_calls[0]
        synack_packet = json.loads(first_synack_call[0][0])
        address = first_synack_call[0][1]

        self.assertEqual(address, self.con.relay_addr)
        self.assertGreater(synack_packet['sequence_number'], 0)
        self.assertLess(synack_packet['sequence_number'], 2**16)

        expected_synack_packet = packet.RUDPPacket(
            synack_packet['sequence_number'],
            self.con.dest_addr,
            self.con.own_addr,
            ack=remote_seqnum + 1,
            syn=True,
        ).to_json()

        for call in m_calls[:-1]:
            self.assertEqual(json.loads(call[0][0]), expected_synack_packet)
            self.assertEqual(call[0][1], address)

        expected_fin_packet = packet.RUDPPacket(
            0,
            self.con.dest_addr,
            self.con.own_addr,
            ack=remote_seqnum + 1,
            fin=True
        ).to_json()

        self.assertEqual(json.loads(m_calls[-1][0][0]), expected_fin_packet)
        self.assertEqual(m_calls[-1][0][1], address)

    def test_receive_synack_during_initial(self):
        remote_synack_packet = packet.RUDPPacket(
            42,
            self.con.own_addr,
            self.con.dest_addr,
            syn=True,
            ack=2**15
        )

        self.con.receive_packet(remote_synack_packet)
        self.assertFalse(self.con.connected)

    def test_receive_normal_during_initial(self):
        remote_normal_packet = packet.RUDPPacket(
            42,
            self.con.own_addr,
            self.con.dest_addr,
            ack=2**15
        )

        self.con.receive_packet(remote_normal_packet)
        self.clock.advance(0)
        connection.REACTOR.runUntilCurrent()

        self.assertFalse(self.con.connected)
        self.handler_mock.receive_message.assert_not_called()

    # == Test CONNECTING state ==

    def _initial_to_connecting(self):
        self.clock.advance(0)
        connection.REACTOR.runUntilCurrent()

    def test_send_syn_during_connecting(self):
        self._initial_to_connecting()

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

        self.assertEqual(address, self.con.relay_addr)
        self.assertGreater(syn_packet['sequence_number'], 0)
        self.assertLess(syn_packet['sequence_number'], 2**16)

        expected_syn_packet = packet.RUDPPacket(
            syn_packet['sequence_number'],
            self.con.dest_addr,
            self.con.own_addr,
            syn=True
        ).to_json()

        for call in m_calls[:-1]:
            self.assertEqual(json.loads(call[0][0]), expected_syn_packet)
            self.assertEqual(call[0][1], address)

        expected_fin_packet = packet.RUDPPacket(
            0,
            self.con.dest_addr,
            self.con.own_addr,
            fin=True
        ).to_json()

        self.assertEqual(json.loads(m_calls[-1][0][0]), expected_fin_packet)
        self.assertEqual(m_calls[-1][0][1], address)

    def test_send_normal_during_connecting(self):
        self._initial_to_connecting()
        
        self.proto_mock.reset_mock()
        self.con.send_message('Yellow Submarine')
        self.clock.advance(0)
        connection.REACTOR.runUntilCurrent()
        m_calls = self.proto_mock.send_datagram.call_args_list
        self.assertEqual(len(m_calls), 0)

    def _connecting_to_connected(self):
        m_calls = self.proto_mock.send_datagram.call_args_list
        sent_syn_packet = json.loads(m_calls[0][0][0])
        seqnum = sent_syn_packet['sequence_number']

        remote_synack_rudppacket = packet.RUDPPacket(
            42,
            self.con.own_addr,
            self.con.dest_addr,
            ack=seqnum + 1,
            syn=True
        )
        self.con.receive_packet(remote_synack_rudppacket)

        self.clock.advance(0)
        connection.REACTOR.runUntilCurrent()

        self.next_seqnum = seqnum + 2
        self.next_acknum = 43

    def test_receive_proper_synack_during_connecting(self):
        self._initial_to_connecting()
        self._connecting_to_connected()

        self.assertTrue(self.con.connected)

    def test_receive_improper_synack_during_connecting(self):
        self._initial_to_connecting()

        m_calls = self.proto_mock.send_datagram.call_args_list
        sent_syn_packet = json.loads(m_calls[0][0][0])
        seqnum = sent_syn_packet['sequence_number']

        remote_synack_rudppacket = packet.RUDPPacket(
            42,
            self.con.own_addr,
            self.con.dest_addr,
            ack=seqnum + 800,
            syn=True
        )
        self.con.receive_packet(remote_synack_rudppacket)

        self.clock.advance(0)
        connection.REACTOR.runUntilCurrent()

        self.assertFalse(self.con.connected)

    def test_receive_fin_during_connecting(self):
        self._initial_to_connecting()

        remote_fin_packet = packet.RUDPPacket(
            0,
            self.con.own_addr,
            self.con.dest_addr,
            fin=True
        )
        self.proto_mock.reset_mock()
        self.con.receive_packet(remote_fin_packet)

        # Trap any calls after shutdown.
        self.clock.advance(100 * constants.PACKET_TIMEOUT)
        connection.REACTOR.runUntilCurrent()

        self.handler_mock.handle_shutdown.assert_called_once_with()

        m_calls = self.proto_mock.send_datagram.call_args_list
        self.assertEqual(len(m_calls), 1)

        fin_call = m_calls[0]
        self.assertEqual(fin_call[0][1], self.con.relay_addr)

        local_fin_packet = json.loads(fin_call[0][0])
        expected_fin_packet = packet.RUDPPacket(
            0,
            self.con.dest_addr,
            self.con.own_addr,
            ack=local_fin_packet['ack'],
            fin=True,
        ).to_json()

        self.assertEqual(local_fin_packet, expected_fin_packet)

    def test_receive_normal_during_connecting(self):
        pass

    # == Test HALF_CONNECTED state ==
    # == Test CONNECTED state ==
    # == Test SHUTDOWN state ==
