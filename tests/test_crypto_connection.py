import mock
from unittest import skipIf

try:
    from nacl import encoding, exceptions, public, utils
except ImportError:
    _NO_PYNACL = True
else:
    _NO_PYNACL = False

from twisted.internet import reactor, task
from twisted.trial import unittest

from txrudp import crypto_connection, connection, constants, packet, rudp

@skipIf(_NO_PYNACL, 'PyNaCl is not installed')
class TestCryptoConnectionAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.public_ip = '123.45.67.89'
        cls.port = 12345
        cls.own_addr = (cls.public_ip, cls.port)
        cls.addr1 = ('132.54.76.98', 54321)
        cls.addr2 = ('231.76.45.89', 15243)
        cls.privkey1_hex = '71d1054068b224a4d9013104881dc7f46c6fec9a618f4574ae21059723e6c4f8'
        cls.privkey1 = public.PrivateKey(
            cls.privkey1_hex,
            encoder=encoding.HexEncoder
        )
        cls.pubkey1 = cls.privkey1.public_key
        cls.pubkey1_bytes = cls.pubkey1.encode(encoder=encoding.RawEncoder)
        
        cls.privkey2_hex = '4c107b7844368d0fb608f3d91ae194f2d62c7ff91b713e5b05c279e8b7fc61b3'
        cls.privkey2 = public.PrivateKey(
            cls.privkey2_hex,
            encoder=encoding.HexEncoder
        )
        cls.pubkey2 = cls.privkey2.public_key
        cls.pubkey2_bytes = cls.pubkey2.encode(encoder=encoding.RawEncoder)

        cls.remote_crypto_box = public.Box(cls.privkey2, cls.pubkey1)
        cls.nonce = utils.random(cls.remote_crypto_box.NONCE_SIZE)

        cls.local_crypto_box = public.Box(cls.privkey1, cls.pubkey2)

        cls.privkey3_hex = '40246691a4362a220606dd302b03e992b5b5fe21026377fa56c9fe3f5afbcbd0'
        cls.privkey3 = public.PrivateKey(
            cls.privkey3_hex,
            encoder=encoding.HexEncoder
        )
        cls.pubkey3 = cls.privkey3.public_key
        cls.pubkey3_bytes = cls.pubkey3.encode(encoder=encoding.RawEncoder)

        cls.other_crypto_box = public.Box(cls.privkey3, cls.pubkey1)

    @classmethod
    def _remote_encrypt_msg(cls, msg):
        return cls.remote_crypto_box.encrypt(msg, cls.nonce)

    @classmethod
    def _other_encrypt_msg(cls, msg):
        return cls.other_crypto_box.encrypt(msg, cls.nonce)

    def setUp(self):
        self.clock = task.Clock()
        connection.REACTOR.callLater = self.clock.callLater

        self.proto_mock = mock.Mock(spec_set=rudp.ConnectionMultiplexer)
        self.handler_mock = mock.Mock(spec_set=connection.Handler)
        self.con = crypto_connection.CryptoConnection(
            self.proto_mock,
            self.handler_mock,
            self.own_addr,
            self.addr1,
            private_key=self.privkey1_hex
        )

    def tearDown(self):
        self.con.shutdown()

    # == Test CONNECTING state ==

    def test_send_syn_during_connecting(self):
        self.clock.advance(0)
        connection.REACTOR.runUntilCurrent()

        self._advance_to_fin()

        m_calls = self.proto_mock.send_datagram.call_args_list
        self.assertEqual(len(m_calls), constants.MAX_RETRANSMISSIONS + 1)

        first_syn_call = m_calls[0]
        syn_packet = packet.Packet.from_bytes(first_syn_call[0][0])
        address = first_syn_call[0][1]

        self.assertEqual(address, self.con.relay_addr)
        self.assertGreater(syn_packet.sequence_number, 0)
        self.assertLess(syn_packet.sequence_number, 2**16)

        expected_syn_packet = packet.Packet.from_data(
            syn_packet.sequence_number,
            self.con.dest_addr,
            self.con.own_addr,
            payload=self.pubkey1_bytes,
            syn=True
        ).to_bytes()

        for call in m_calls[:-1]:
            self.assertEqual(call[0][0], expected_syn_packet)
            self.assertEqual(call[0][1], address)

        expected_fin_packet = packet.Packet.from_data(
            0,
            self.con.dest_addr,
            self.con.own_addr,
            fin=True
        ).to_bytes()

        self.assertEqual(m_calls[-1][0][0], expected_fin_packet)
        self.assertEqual(m_calls[-1][0][1], address)

    def _advance_to_fin(self):
        for _ in range(constants.MAX_RETRANSMISSIONS):
            # Each advance forces a SYN packet retransmission.
            self.clock.advance(constants.PACKET_TIMEOUT)

        # Force transmission of FIN packet and shutdown.
        self.clock.advance(constants.PACKET_TIMEOUT)

        # Trap any calls after shutdown.
        self.clock.advance(100 * constants.PACKET_TIMEOUT)
        connection.REACTOR.runUntilCurrent()

    def test_send_casual_during_connecting(self):
        self.con.send_message(b'Yellow Submarine')
        self.clock.advance(100 * constants.PACKET_TIMEOUT)
        connection.REACTOR.runUntilCurrent()

        m_calls = self.proto_mock.send_datagram.call_args_list
        self.assertEqual(len(m_calls), 1)
        p = packet.Packet.from_bytes(m_calls[0][0][0])
        self.assertTrue(p.syn)
        self.assertEqual(p.payload, self.pubkey1_bytes)

    def test_receive_fin_during_connecting(self):
        fin_rudp_packet = packet.Packet.from_data(
            0,
            self.con.own_addr,
            self.con.dest_addr,
            fin=True
        )

        self.con.receive_packet(fin_rudp_packet)
        self.clock.advance(0)
        connection.REACTOR.runUntilCurrent()

        self.assertEqual(self.con.state, connection.State.CONNECTING)
        self.handler_mock.handle_shutdown.assert_not_called()

    def test_receive_ack_during_connecting(self):
        pass

    def test_receive_syn_during_connecting(self):
        remote_seqnum = 42
        remote_syn_packet = packet.Packet.from_data(
            remote_seqnum,
            self.con.own_addr,
            self.con.dest_addr,
            payload=self.pubkey2_bytes,
            syn=True
        )

        self.con.receive_packet(remote_syn_packet)
        self.clock.advance(0)
        connection.REACTOR.runUntilCurrent()
        self.assertEqual(self.con.state, connection.State.CONNECTED)
        self.assertEqual(self.con.remote_public_key, self.pubkey2_bytes)

    def test_receive_bad_syn_during_connecting(self):
        remote_seqnum = 42
        remote_syn_packet = packet.Packet.from_data(
            remote_seqnum,
            self.con.own_addr,
            self.con.dest_addr,
            payload='udfglaidufgalksdfjgalsdf',  # not a public key
            syn=True
        )

        self.con.receive_packet(remote_syn_packet)
        self.clock.advance(0)
        connection.REACTOR.runUntilCurrent()
        self.assertEqual(self.con.state, connection.State.CONNECTING)
        self.assertIsNone(self.con.remote_public_key)

    def test_receive_casual_during_connecting(self):
        remote_casual_packet = packet.Packet.from_data(
            42,
            self.con.own_addr,
            self.con.dest_addr,
            payload=b'Yellow Submarine',
            ack=2**15
        )

        self.con.receive_packet(remote_casual_packet)
        self.clock.advance(0)
        connection.REACTOR.runUntilCurrent()

        self.assertEqual(self.con.state, connection.State.CONNECTING)
        self.handler_mock.receive_message.assert_not_called()

    # == Test CONNECTED state ==

    def _connecting_to_connected(self):
        remote_syn_packet = packet.Packet.from_data(
            42,
            self.con.own_addr,
            self.con.dest_addr,
            payload=self.pubkey2_bytes,
            syn=True
        )
        self.con.receive_packet(remote_syn_packet)

        self.clock.advance(0)
        connection.REACTOR.runUntilCurrent()

        self.next_remote_seqnum = 43

        m_calls = self.proto_mock.send_datagram.call_args_list
        sent_syn_packet = packet.Packet.from_bytes(m_calls[0][0][0])
        seqnum = sent_syn_packet.sequence_number

        self.handler_mock.reset_mock()
        self.proto_mock.reset_mock()

        self.next_seqnum = seqnum + 1

    def test_send_casual_message_during_connected(self):
        self._connecting_to_connected()
        self.con.send_message(b'Yellow Submarine')
        self._advance_to_fin()

        # Filter casual packets.
        sent_packets = tuple(
            packet.Packet.from_bytes(call[0][0])
            for call in self.proto_mock.send_datagram.call_args_list
        )
        sent_casual_datagrams = tuple(
            sent_packet.to_bytes()
            for sent_packet in sent_packets
            if not (sent_packet.syn or sent_packet.fin)
        )

        self.assertEqual(
            len(sent_casual_datagrams),
            constants.MAX_RETRANSMISSIONS
        )

        ciphertext = packet.Packet.from_bytes(
            sent_casual_datagrams[0]
        ).payload
        plaintext = self.remote_crypto_box.decrypt(ciphertext)
        self.assertEqual(plaintext, b'Yellow Submarine')

    def test_send_ack_during_connected(self):
        self._connecting_to_connected()

        remote_casual_packet = packet.Packet.from_data(
            self.next_remote_seqnum,
            self.con.own_addr,
            self.con.dest_addr,
            payload=self._remote_encrypt_msg(b'Yellow Submarine'),
            ack=self.next_seqnum
        )
        self.con.receive_packet(remote_casual_packet)

        self.clock.advance(constants.BARE_ACK_TIMEOUT)
        connection.REACTOR.runUntilCurrent()

        m_calls = self.proto_mock.send_datagram.call_args_list

        # Filter bare ACK packets.
        sent_packets = (
            packet.Packet.from_bytes(call[0][0])
            for call in self.proto_mock.send_datagram.call_args_list
        )
        sent_bare_ack_packets = tuple(
            sent_packet
            for sent_packet in sent_packets
            if sent_packet.ack > 0 and sent_packet.sequence_number == 0
        )

        self.assertEqual(len(sent_bare_ack_packets), 1)
        bare_ack_packet = sent_bare_ack_packets[0]

        try:
            self.local_crypto_box.decrypt(bare_ack_packet.payload)
        except (
            exceptions.CryptoError,
            exceptions.BadSignatureError,
            ValueError
        ):
            self.fail('Outbound ACK packet was not encrypted.')

    def test_receive_casual_packet_during_connected(self):
        self._connecting_to_connected()

        remote_casual_packet = packet.Packet.from_data(
            self.next_remote_seqnum,
            self.con.own_addr,
            self.con.dest_addr,
            payload=self._remote_encrypt_msg(b'Yellow Submarine'),
            ack=self.next_seqnum
        )
        self.con.receive_packet(remote_casual_packet)

        self.clock.advance(0)
        connection.REACTOR.runUntilCurrent()

        self.handler_mock.receive_message.assert_called_once_with(
            b'Yellow Submarine'
        )

    def test_receive_rogue_casual_packet_during_connected(self):
        self._connecting_to_connected()

        remote_casual_packet = packet.Packet.from_data(
            self.next_remote_seqnum,
            self.con.own_addr,
            self.con.dest_addr,
            payload=self._other_encrypt_msg(b'Yellow Submarine'),
            ack=self.next_seqnum
        )
        self.con.receive_packet(remote_casual_packet)

        self.clock.advance(0)
        connection.REACTOR.runUntilCurrent()

        self.handler_mock.receive_message.assert_not_called()

    # == Test SHUTDOWN state ==

    def test_send_casual_during_shutdown(self):
        self._connecting_to_connected()
        self.con.shutdown()

        self.con.send_message("Yellow Submarine")

        self.clock.advance(100 * constants.PACKET_TIMEOUT)
        connection.REACTOR.runUntilCurrent()

        self.assertEqual(self.con.state, connection.State.SHUTDOWN)
        self.proto_mock.send_datagram.assert_not_called()

    def test_receive_syn_during_shutdown(self):
        pass

    def test_receive_synack_during_shutdown(self):
        pass

    def test_receive_ack_during_shutdown(self):
        pass

    def test_receive_fin_during_shutdown(self):
        pass

    def test_receive_casual_during_shutdown(self):
        self._connecting_to_connected()
        self.con.shutdown()

        self.handler_mock.reset_mock()

        casual_rudp_packet = packet.Packet.from_data(
            self.next_seqnum,
            self.con.dest_addr,
            self.con.own_addr,
            ack=0,
            payload=b'Yellow Submarine'
        )
        self.con.receive_packet(casual_rudp_packet)

        self.clock.advance(100 * constants.PACKET_TIMEOUT)
        connection.REACTOR.runUntilCurrent()

        self.assertEqual(self.con.state, connection.State.SHUTDOWN)
        self.handler_mock.receive_message.assert_not_called()
