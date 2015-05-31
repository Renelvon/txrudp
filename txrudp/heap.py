"""Simple heap used as reorder buffer for received packets."""

import collections
import heapq


class EmptyHeap(Exception):

    """Raised when popping from empty heap."""


class Heap(collections.Sequence):

    """
    A min-heap for packets implementing total ordering.

    The packet with the minimum sequence number is always at the
    front of the sequence, i.e at index 0.
    """

    def __init__(self):
        """Create a new (empty) Heap."""
        self._heap = []
        self._seqnum_set = set()

    def __getitem__(self, index):
        """
        Get packet at given index.

        Args:
            index: The index of the requested packet.

        Returns:
            Packet at given index. The only packet guaranteed
            to have a specific seqnum is the one at index 0, which
            shall be the packet with the minimum seqnum in the heap
            (assuming a non-empty heap.)
        Raises:
            IndexError: No packet resides in given index.
        """
        return self._heap[index]

    def __len__(self):
        """Return number of packets inside heap."""
        return len(self._heap)

    def push(self, rudp_packet):
        """
        Push a new packet in the heap.

        Args:
            rudp_packet: A packet.RUDPPacket.
        """
        heapq.heappush(self._heap, rudp_packet)
        self._seqnum_set.add(rudp_packet.sequence_number)

    def pop_min(self):
        """
        Pop the packet at the top of the heap.

        Returns:
            A packet.RUDPPacket

        Raises:
            EmptyHeap: The heap is empty.
            KeyError: The packet's sequence number is not listed
                in the seqnum set; some invariant has been violated.
        """
        try:
            rudp_packet = heapq.heappop(self._heap)
        except IndexError:
            raise EmptyHeap('Cannot pop from empty heap.')
        else:
            self._seqnum_set.remove(rudp_packet.sequence_number)
            return rudp_packet

    def attempt_popping_all_fragments(self, sequence_number):
        """
        Attempt to pop all fragments of packet with given seqnum.

        This will only succeed if the said packet is at the top
        of the heap and all its other fragments reside in the heap.
        In such a case all the fragments of the said packet are
        popped from the heap and returned in order.

        Args:
            sequence_number: The sequence_number of the target packet.

        Returns:
            Tuple of packet.RUDPPackets, ordered by increasing seqnum,
            or None if operation was unsuccessful for any reason.
        """
        if not self._heap:
            return None

        min_packet = self._heap[0]
        if min_packet.sequence_number != sequence_number:
            return None

        fragments_seqnum_set = set(
            min_packet.sequence_number + i
            for i in range(min_packet.more_fragments + 1)
        )
        if not fragments_seqnum_set.issubset(self._seqnum_set):
            return None

        # If all the requirements are satisfied, then, because the
        # fragments have 'sequential' sequence numbers, we can get all
        # of them with repeated calls to `pop_min`.
        return tuple(
            self._heap.pop_min()
            for _ in range(min_packet.more_fragments + 1)
        )
