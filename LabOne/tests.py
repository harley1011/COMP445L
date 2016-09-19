import unittest
import http
# Run using the command python -m unittest tests
class TestHttp(unittest.TestCase):

    def test_http(self):
        #http.post("http://www.test.com", 80)
        self.assertTrue(True, True)

    def test_request_header(self):
        result = http.request_line('GET', 'http://www.test.com', 'HTTP/1.0')
        print(result)

if __name__ == '__main__':
    unittest.main()