import collections

from twisted.internet import reactor
from twisted.trial import unittest as trialtest

from txrudp import connection, packet


class TestScheduledPacketAPI(trialtest.TestCase):

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
