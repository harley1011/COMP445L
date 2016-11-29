import unittest
import time
import lib.tcp as tcp
import lib.connection_status as connection_status


# Run using the command python3 -m unittest tests
class TestHttp(unittest.TestCase):
    # Make sure the router is running on port 3000

    def test_simple(self):
        tcp_listener = tcp.Tcp('localhost', 3000)
        tcp_sender = tcp.Tcp('localhost', 3000)

        tcp_listener.start_listening(5666)
        time.sleep(1)
        # self.assertEquals(tcp_listener.connection_status, connection_status.ConnectionStatus.Listening)

        tcp_sender.send('localhost', 5666, "Hello world".encode())

        conn, addr = tcp_listener.accept()

        time.sleep(5)

        result = conn.recv_from(100)
        self.assertEquals(result, "Hello world".encode())

        self.assertEquals(result, "Hello world".encode())
        for i in range(0, 10):
            print("Try number {}\r\n\r\n\r\n".format(i + 1))
            message = "Hello world{0}".format(i + 1).encode()
            tcp_sender.send('localhost', 5666, message)
            result = conn.recv_from(100)
            self.assertEquals(result, message)

        self.assertEquals(conn.connection_status, connection_status.ConnectionStatus.Open)
        self.assertEquals(tcp_sender.connection_status, connection_status.ConnectionStatus.Open)

        conn.close()
        tcp_listener.close()

    def test_multiple_sequential(self):
        number_of_connections = 15
        tcp_listener = tcp.Tcp('localhost', 3000)
        tcp_senders = []
        for i in range(0, number_of_connections):
            tcp_senders.append(tcp.Tcp('localhost', 3000))

        tcp_listener.start_listening(5666)
        time.sleep(1)
        for i in range(0, number_of_connections):
            print("Try number {}\r\n\r\n\r\n".format(i + 1))
            message = "Hello world{0}".format(i + 1).encode()
            tcp_sender = tcp_senders[i]
            tcp_sender.send('localhost', 5666, message)

            conn, addr = tcp_listener.accept()
            result = conn.recv_from(100)
            self.assertEquals(result, message)
            self.assertEquals(conn.connection_status, connection_status.ConnectionStatus.Open)
            self.assertEquals(tcp_sender.connection_status, connection_status.ConnectionStatus.Open)
            conn.close()

        tcp_listener.close()

    def test_large_payload(self):
        tcp_listener = tcp.Tcp('localhost', 3000)
        tcp_sender = tcp.Tcp('localhost', 3000)

        tcp_listener.start_listening(5666)
        time.sleep(1)
        f = open('./testfiles/body4.txt', 'r')
        body = f.read()
        f.close()

        tcp_sender.send('localhost', 5666, body.encode())

        conn, addr = tcp_listener.accept()

        time.sleep(40)

        count = 0
        buf = bytearray()
        body_count = len(body)
        while count < body_count:
            read_bytes_num = body_count - count
            if read_bytes_num > 1000:
                read_bytes_num = 1000
            result = conn.recv_from(read_bytes_num)
            count += read_bytes_num
            buf.extend(result)
        self.assertEquals(buf, body.encode())
        self.assertEquals(conn.connection_status, connection_status.ConnectionStatus.Open)
        self.assertEquals(tcp_sender.connection_status, connection_status.ConnectionStatus.Open)

        conn.close()
        tcp_listener.close()




