"""Constants governing operation of txrudp package."""

# [bytes]
UDP_SAFE_PACKET_SIZE = 1000

# [length]
WINDOW_SIZE = 65535 // UDP_SAFE_PACKET_SIZE

# [seconds]
TIMEOUT = 0.7

# [seconds]
_MAX_PACKET_DELAY = 20

# If a packet is retransmitted more than that many times,
# the connection should be considered broken.
MAX_RETRANSMISSIONS = _MAX_PACKET_DELAY // TIMEOUT
