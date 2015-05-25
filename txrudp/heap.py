"""Simple heap used as reorder buffer for received messages."""

import collections
import heapq


class EmptyHeap(Exception):

    """Raised when popping from empty heap."""


class Heap(collections.Sequence):

    """
    A min-heap for objects implementing total ordering.

    The object with the minium order number is always at the front
    of the sequence, i.e at index 0.
    """

    def __init__(self):
        """Create a new (empty) Heap."""
        self._heap = []

    def __getitem__(self, index):
        """
        Get object at given index.

        Args:
            index: The index of the requested object.

        Returns:
            Object at given index. The only object guaranteed
            to have a specific value is the one at index 0, which
            shall be the minimum object in the heap (assuming
            a non-empty heap.)
        Raises:
            IndexError: No element resides in given index.
        """
        return self._heap[index]

    def __len__(self):
        """Return number of objects inside heap."""
        return len(self._heap)

    def push(self, obj):
        """
        Push a new object in the heap.

        Args:
            obj: An object supporting total ordering.
        """
        heapq.heappush(self._heap, obj)

    def pop_min(self):
        """
        Pop the object at the top of the heap.

        Raises:
            EmptyHeap: The heap is empty.
        """
        try:
            return heapq.heappop(self._heap)
        except IndexError:
            raise EmptyHeap('Cannot pop from empty heap.')
