import unittest
import http
# Run using the command python -m unittest tests
class TestHttp(unittest.TestCase):

    def test_http(self):
        http.post("http://www.test.com", 80)
        self.assertTrue(True, True)

if __name__ == '__main__':
    unittest.main()