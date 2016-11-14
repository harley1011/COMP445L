from enum import Enum


class ConnectionStatus(Enum):
    Closed = 0
    Handshake = 1
    Open = 2
