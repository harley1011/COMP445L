import unittest
import lib.httpc as httpc
import http.client
import json


# Run using the command python3 -m unittest tests
class TestHttp(unittest.TestCase):

    def test_http_get_method_google(self):
        httpc_connection = httpc.HttpConnection("www.google.com", 80)
        httpc_connection.request('GET', '')
        httpc_response = httpc_connection.getresponse()
        httpc_connection.close()

        self.assertEquals(httpc_response.status_code, 302)

    def test_http_get_method_without_parameters(self):
        # Test our library
        httpc_connection = httpc.HttpConnection("www.httpbin.org", 80)
        httpc_connection.request('GET', '/status/418')
        httpc_response = httpc_connection.getresponse()
        httpc_connection.close()

        # Test against pythons official HTTP library
        conn = http.client.HTTPSConnection("www.httpbin.org")
        conn.request("GET", "/status/418")
        http_response = conn.getresponse()
        http_response_body = http_response.read().decode("utf-8")
        conn.close()

        self.assertEqual(httpc_response.body, http_response_body)
        self.assertEquals(httpc_response.status_code, http_response.status)

    def test_http_get_method_with_parameters(self):
        httpc_connection = httpc.HttpConnection("www.httpbin.org", 80)
        httpc_connection.request('GET', '/get?course=networking&assignment=1')
        httpc_response = httpc_connection.getresponse()
        httpc_response_args = json.loads(httpc_response.body)['args']
        httpc_connection.close();

        conn = http.client.HTTPSConnection("www.httpbin.org")
        conn.request("GET", "/get?course=networking&assignment=1")
        http_response = conn.getresponse()
        http_response_body = http_response.read().decode("utf-8")
        http_response_args = json.loads(http_response_body)['args']
        conn.close()
        self.assertEqual(httpc_response_args, http_response_args)
        self.assertEquals(httpc_response.status_code, http_response.status)

    def test_http_get_method_without_parameters_img(self):
        httpc_connection = httpc.HttpConnection("www.httpbin.org", 80)
        httpc_connection.request('GET', '/image/png')
        httpc_response = httpc_connection.getresponse()
        httpc_connection.close()

        conn = http.client.HTTPSConnection("www.httpbin.org")
        conn.request("GET", "/image/png")
        http_response = conn.getresponse()
        http_response_body = http_response.read()
        conn.close()
        self.assertEqual(httpc_response.body, http_response_body)
        self.assertEquals(httpc_response.status_code, http_response.status)

    def test_http_post_method_without_parameters(self):
        body = "comments=&custemail=harley.1011%40gmail.com&custname=Harley&delivery=&size=small&topping=bacon"
        httpc_connection = httpc.HttpConnection("www.httpbin.org", 80)
        headers = {}
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        headers['Content-Length'] = len(body)
        headers['Accept-Encoding'] = 'identity'
        httpc_connection.request('POST', '/post', body, headers)
        httpc_response = httpc_connection.getresponse()
        httpc_connection.close()

        conn = http.client.HTTPSConnection("www.httpbin.org")
        conn.request("POST", "/post", body,headers)
        http_response = conn.getresponse()
        http_response_body = http_response.read().decode('utf-8')
        conn.close()
        self.assertEqual(json.loads(httpc_response.body)['form'], json.loads(http_response_body)['form'])
        self.assertEqual(httpc_response.status_code, 200)


if __name__ == '__main__':
    unittest.main()