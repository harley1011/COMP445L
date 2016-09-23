import unittest
import lib.httpc as httpc
import http.client


# Run using the command python3 -m unittest tests
class TestHttp(unittest.TestCase):

    def test_http_get_method_without_parameters(self):
        http_connection = httpc.HttpConnection("www.httpbin.org", 80)
        http_connection.request('GET', '/status/418')
        httpc_response = http_connection.getresponse()

        conn = http.client.HTTPSConnection("www.httpbin.org")
        conn.request("GET", "/status/418")
        http_response = conn.getresponse()
        http_response_body = http_response.read().decode("utf-8")
        conn.close()
        self.assertEqual(httpc_response.body, http_response_body)
        self.assertEquals(httpc_response.status_code, http_response.status)

    def test_http_get_method_with_parameters(self):
        http_connection = httpc.HttpConnection("www.httpbin.org", 80)
        http_connection.request('GET', '/get?course=networking&assignment=1')
        httpc_response = http_connection.getresponse()

        conn = http.client.HTTPSConnection("www.httpbin.org")
        conn.request("GET", "/get?course=networking&assignment=1")
        http_response = conn.getresponse()
        http_response_body = http_response.read().decode("utf-8")
        conn.close()
        self.assertEqual(httpc_response.body, http_response_body)
        self.assertEquals(httpc_response.status_code, http_response.status)


if __name__ == '__main__':
    unittest.main()