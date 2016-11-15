import unittest
import time
import lib.tcp as tcp
import lib.connection_status as connection_status


# Run using the command python3 -m unittest tests
class TestHttp(unittest.TestCase):
    # Make sure the router is running on port 3000

    def test__handshake(self):
        tcp_listener = tcp.Tcp('localhost', 3000)
        tcp_sender = tcp.Tcp('localhost', 3000)

        tcp_listener.start_listening(5666)
        time.sleep(1)
        self.assertEquals(tcp_listener.connection_status, connection_status.ConnectionStatus.Listening)

        # tcp_sender.send('localhost', 5666, "hello")

        f = open('../ltwo/testfiles/body1.txt', 'r')
        body = f.read()
        f.close()

        tcp_sender.send('localhost', 5666, body)

        time.sleep(5)
        self.assertEquals(tcp_listener.connection_status, connection_status.ConnectionStatus.Open)
        self.assertEquals(tcp_sender.connection_status, connection_status.ConnectionStatus.Open)



