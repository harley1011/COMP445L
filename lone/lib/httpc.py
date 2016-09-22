import socket
import re
from urllib.parse import urlparse


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
        self.headers = self.format_headers(headers)
        request_line = self.create_request_line(method, path, self.http_version)
        request_message = '{}\r\n{}'.format(request_line, self.headers)
        response = self.tcp_send(self.host, self.port, request_message)
        self.response = response.decode('utf-8')

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
        return '{} {} {}\n\n'.format(method_type, url, version)

    def tcp_send(self, host, port, message):
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((host, port))
        tcp_socket.sendall(message.encode())
        response = tcp_socket.recv(4096)
        tcp_socket.close()
        return response


if __name__ == '__main__':
    HttpConnection()



class HttpResponse(object):
    def __init__(self, response):
        response = response.split('\r\n')

        status_line = response.pop(0).split(' ')
        self.http_version = status_line[0]
        self.status_code = status_line[1]
        self.reason_phrase = status_line[2]
        self.headers = {}

        while len(response) > 0:
            header = response.pop(0)

            if header == '':
                break

            header = header.split(": ", 1)
            self.headers[header[0]] = header[1]



        self.body = ''
        self.headers = ''
        self.http_version = ''






class InvalidRequest(Exception):
    def __init__(self, message):
        self.message = message
