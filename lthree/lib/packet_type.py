from enum import Enum


class PacketType(Enum):
    SYN = 0
    ACK = 1
    SYN_ACK = 2,
    DATA = 3
