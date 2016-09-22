import unittest
import lib.httpc as httpc
import http.client


# Run using the command python3 -m unittest tests
class TestHttp(unittest.TestCase):

    def test_http_get_method_without_parameters(self):
        http_connection = httpc.HttpConnection("http://httpbin.org/status/418", "HTTP/1.0")
        http_connection.get()
        result = http_connection.getResponse()

        conn = http.client.HTTPSConnection("www.httpbin.org")
        conn.request("GET", "/status/418")
        actual_result = conn.getresponse().read().decode("utf-8")
        conn.close()
        print(result)
        self.assertEquals(result, actual_result)

    def test_http_get_method_with_parameters(self):
        http_connection = httpc.HttpConnection("http://httpbin.org/get?course=networking&assignment=1", "HTTP/1.0")
        http_connection.get()
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()