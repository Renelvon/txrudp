"""Constants governing operation of txrudp package."""

# [bytes]
UDP_SAFE_PACKET_SIZE = 1000

# [length]
WINDOW_SIZE = 65535 // UDP_SAFE_PACKET_SIZE

# [seconds]
PACKET_TIMEOUT = 0.7

# [seconds]
BARE_ACK_TIMEOUT = 0.3

# [seconds]
KEEP_ALIVE_TIMEOUT = 5

# [seconds]
MAX_PACKET_DELAY = 20

# If a packet is retransmitted more than that many times,
# the connection should be considered broken.
MAX_RETRANSMISSIONS = int(MAX_PACKET_DELAY // PACKET_TIMEOUT)
