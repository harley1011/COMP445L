import unittest

import lib.tcp as tcp


class TestHttp(unittest.TestCase):
    # Make sure the router is running on port 3000

    def test__handshake(self):
        tcp_listener = tcp.Tcp('localhost', 3000)
        tcp_sender = tcp.Tcp('localhost', 3000)
