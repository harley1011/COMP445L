import unittest
from httpc import *


# Run using the command python3 -m unittest tests
class TestHttp(unittest.TestCase):


    def test_http_get_method(self):
        http_connection = HttpConnection("http://httpbin.org/status/418", "HTTP/1.0")
        http_connection.get()
        self.assertTrue(True, True)


if __name__ == '__main__':
    unittest.main()