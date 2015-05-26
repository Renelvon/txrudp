"""Reliable UDP implementation using Twisted."""

import collections

from twisted.internet import protocol


class ConnectionMultiplexer(
    protocol.DatagramProtocol,
    collections.MutableMapping
):

    """
    Multiplexes many virtual connections over single UDP socket.

    Handles graceful shutdown of active connections.
    """

    def __init__(self, connection_factory):
        """
        Initialize a new multiplexer.

        Args:
            connection_factory: The connection factory used to instantiate
                new connections, as a connection.RUDPConnectionFactory.
        """
        super(ConnectionMultiplexer, self).__init__()
        self._active_connections = {}
        self._connection_factory = connection_factory

    def __len__(self):
        """Return the number of live connections."""
        return len(self._active_connections)

    def __getitem__(self, addr):
        """
        Return the handling connection of the given address.

        Args:
            addr: Tuple of destination address (ip, port).

        Raises:
            KeyError: No connection is handling the given address.
        """
        return self._active_connections[addr]

    def __setitem__(self, addr, con):
        """
        Register a handling connection for a given remote address.

        If a previous connection is already bound to that address,
        it is shutdown and then replaced.

        Args:
            key: Tuple of destination address (ip, port).
            value: The connection to register, as an RUDPConnection
        """
        prev_con = self._active_connections.get(addr)
        if prev_con is not None:
            prev_con.shutdown()
        self._active_connections[addr] = con

    def __delitem__(self, addr):
        """
        Unregister a handling connection for a given remote address.

        Args:
            addr: Tuple of destination address (ip, port).

        Raises:
            KeyError: No connection is handling the given address.
        """
        del self._active_connections[addr]

    def __iter__(self):
        """Return iterator over the active contacts."""
        return iter(self._active_connections)

    def datagramReceived(self, datagram, addr):
        """
        Called when a datagram is received.

        Args:
            datagram: Datagram string received from transport layer.
            addr: Sender address, as a tuple of an IPv4/IPv6 address
                and a port, in that order.
        """
        con = self._active_connections.get(addr)
        if con is None:
            con = self.make_new_connection(addr)
        con.receive_packet(datagram)

    def make_new_connection(self, addr):
        """
        Create a new connection to handle the given address.

        Args:
            addr: Tuple of destination address (ip, port).

        Returns:
            A new connection.RUDPConnection
        """
        con = self._connection_factory.make_new_connection(self, addr)
        self._active_connections[addr] = con
        return con

    def send_datagram(self, datagram, addr):
        """
        Send RUDP datagram to the given address.

        Args:
            datagram: Prepared RUDP datagram, as a string.
            addr: Tuple of destination address (ip, port).

        This is essentially a wrapper so that the transport layer is
        not exposed to the connections.
        """
        self.transport.write(datagram, addr)

    def shutdown(self):
        """Shutdown all active connections and then terminate protocol."""
        for connection in self._active_connections:
            connection.shutdown()
        self.transport.loseConnection()
