import socket


class HttpConnection(object):
    def __init__(self, host, port=None, version='HTTP/1.0', output=True, redirect=True):
        self.host = host
        self.http_version = version
        self.headers = ''
        self.method = 'GET'
        self.path = ''
        self.body = ''
        self.response = ''
        self.request_message = ''
        self.output = output
        self.redirect = redirect
        if port is not None:
            self.port = port
        else:
            self.port = 80
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.connect((host, port))

    def request(self, method, path, body=None, headers={}, agent=None):
        if method != 'GET' and method != 'POST':
            raise InvalidRequest('{} is not a supported method type'.format(method))
        if len(path) == 0:
            path = '/'
        if method == 'POST':
            headers['Content-Length'] = len(body)

        self.method = method
        self.path = path
        self.body = body
        self.headers = 'Host: {}\r\n'.format(self.host)
        if agent is not None:
            self.headers = '{}Agent: {}\r\n'.format(self.headers, agent)

        self.headers = self.headers + self.format_headers(headers)
        request_line = self.create_request_line(method, path, self.http_version)
        self.request_message = '{}\r\n{}'.format(request_line, self.headers)

        if body is not None and len(body) > 0:
            self.request_message = '{}\r\n{}'.format(self.request_message, body)

        self.request_message = '{}\r\n'.format(self.request_message)
        response = self.tcp_send(self.request_message)
        http_response = HttpResponse(response)
        self.response = http_response

        if self.output:
            lines = self.request_message.split('\r\n')
            for line in lines:
                print('> {}\n'.format(line), end="")
            lines = http_response.response_details.split('\r\n')
            for line in lines:
                print('< {}\n'.format(line), end="")
            print('<')

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

    def close(self):
        self.tcp_socket.close()

    def tcp_send(self, message):
        self.tcp_socket.sendall(message.encode())
        response = bytearray()
        try:
            while True:
                data = self.tcp_socket.recv(4096)
                if not data:
                    break
                else:
                    response.extend(data)
        finally:
            return response


class HttpResponse(object):
    def __init__(self, response):
        self.raw_response = response
        response = response.split(b'\r\n\r\n', 1)
        self.response_details = response[0].decode('utf-8')
        response_header = response[0].decode('utf-8').split('\r\n', 1)
        response_body = response[1]

        status_line = response_header.pop(0).split(' ')
        response_header = response_header[0].split('\r\n')
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
            decode_type = 'utf-8'
            if 'Content-Type' in self.headers and 'charset=' in self.headers['Content-Type']:
                decode_type = self.headers['Content-Type'].split('charset=')[1]
            self.body = response_body.decode(decode_type)
        except:
            self.body = response_body


class InvalidRequest(Exception):
    def __init__(self, message):
        self.message = message
