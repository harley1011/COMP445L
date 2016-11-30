import unittest
import time
import lib.tcp as tcp
import lib.connection_status as connection_status
import threading

import main
import server
from multiprocessing.pool import ThreadPool

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
            print("\r\nTry number {}\r\n".format(i + 1))
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
            print("\r\nTry number {}\r\n".format(i + 1))
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

        count = 0
        buf = bytearray()
        body_count = len(body)
        timer = time.time()
        while count < body_count:
            print("\r\n{} bytes received\r\n".format(count))
            read_bytes_num = body_count - count
            if read_bytes_num > 1000:
                read_bytes_num = 1000
            result = conn.recv_from(read_bytes_num)
            buf.extend(result)
            count = len(buf)
        self.assertEquals(len(buf), len(body.encode()))
        self.assertEquals(buf, body.encode())
        self.assertEquals(conn.connection_status, connection_status.ConnectionStatus.Open)
        self.assertEquals(tcp_sender.connection_status, connection_status.ConnectionStatus.Open)
        elapsed = time.time() - timer
        print('{} bytes/s'.format(body_count/elapsed))
        conn.close()
        tcp_listener.close()

    def test_http_get_file(self):
        threading.Thread(target=server.main, args=([['-v', '-p', '5666', '-d', './testfiles']]), daemon=True).start()
        result = main.main(['get', '-v', '127.0.0.1/ex.html'])
        f = open('./testfiles/ex.html', 'r')
        self.assertEquals(result.getresponse().body, f.read())

    def test_http_get_huge_file(self):
        threading.Thread(target=server.main, args=([['-v', '-p', '5666', '-d', './testfiles']]), daemon=True).start()
        result = main.main(['get', '-v', '127.0.0.1/100kb.txt'])
        f = open('./testfiles/100kb.txt', 'r')
        self.assertEquals(result.getresponse().body, f.read())

    def test_http_parallel_get_file(self):
        threading.Thread(target=server.main, args=([['-v', '-p', '5666', '-d', './testfiles']]), daemon=True).start()
        async_results = []
        number_of_requests = 10
        for i in range(0, number_of_requests):
            print(" Starting Thread " + str(i))
            pool = ThreadPool(processes=1)
            async_result = pool.apply_async(main.main, [['get', '-v', '127.0.0.1/ex.html']])
            async_results.append(async_result)
        f = open('./testfiles/ex.html', 'r')
        file_text = f.read()
        f.close()
        for i in range(0, number_of_requests):
            print("Waiting for thread " + str(i))
            result = async_result.get()
            self.assertEquals(result.getresponse().body, file_text)






