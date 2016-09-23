import socket


class HttpConnection(object):
    def __init__(self, host, port=None, version='HTTP/1.0'):
        self.host = host
        self.http_version = version
        self.headers = ''
        self.method = 'GET'
        self.path = ''
        self.body = ''
        self.response = ''
        if port is not None:
            self.port = port
        else:
            self.port = 80

    def request(self, method, path, body=None, headers={}):
        if method != 'GET' and method != 'POST':
            raise InvalidRequest('{} is not a supported method type'.format(method))
        self.method = method
        self.path = path
        self.body = body
        self.headers = 'Host: ' + self.host + '\r\n'
        self.headers = self.headers + self.format_headers(headers)
        request_line = self.create_request_line(method, path, self.http_version)
        if len(self.headers) > 0:
            request_message = '{}\r\n{}'.format(request_line, self.headers)
        else:
            request_message = request_line + '\r\n'

        if self.body is not None and len(self.body) > 0:
            request_message = '{}\r\n{}'.format(request_message, self.body)
        request_message = request_message + '\r\n'
        response = self.tcp_send(self.host, self.port, request_message)
        http_response = HttpResponse(response)
        self.response = http_response

    @staticmethod
    def format_headers(headers):
        headers_string = ''
        for key, value in headers.items():
            headers_string += '{}: {}\r\n'.format(key, value)
        return headers_string

    def getresponse(self):
        return self.response

    @staticmethod
    def create_request_line(method_type, url, version):
        return '{} {} {}'.format(method_type, url, version)

    def tcp_send(self, host, port, message):
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((host, port))
        tcp_socket.sendall(message.encode())
        response = bytearray()
        while True:
            data = tcp_socket.recv(4096)
            if not data:
                break
            else:
                response.extend(data)

        tcp_socket.close()
        return response


class HttpResponse(object):
    def __init__(self, response):
        self.raw_response = response
        response = response.split(b'\r\n\r\n')
        response_header = response[0].decode('utf-8').split('\r\n')
        response_body = response[1]

        status_line = response_header.pop(0).split(' ')
        self.http_version = status_line[0]
        self.status_code = int(status_line[1])
        self.reason_phrase = status_line[2]
        self.headers = {}

        while len(response_header) > 0:
            header = response_header.pop(0)

            if header == '':
                break

            header = header.split(": ", 1)
            self.headers[header[0]] = header[1]

        try:
            self.body = response_body.decode('utf-8')
        except:
            self.body = response_body


class InvalidRequest(Exception):
    def __init__(self, message):
        self.message = message
