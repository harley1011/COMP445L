import socket
from urllib.parse import urlparse


class HttpConnection(object):
    def __init__(self, host, version):
        self.connection_info = urlparse(host)
        self.http_version = version

    def post(self):
        self.create_request_line('POST', self.connection_info.path, self.http_version)

    def get(self):
        path = self.connection_info.path
        if self.connection_info.query is not None and len(self.connection_info.query) > 0:
            path = '{}?{}'.format(path, self.connection_info.query)
        request_line = self.create_request_line('GET', path, self.http_version)
        response = self.tcp_send('www.' + self.connection_info.netloc,80, request_line)
        self.response = response.decode("utf-8")


    def getResponse(self):
        return self.response
    # Request-Line   = Method SP Request-URI SP HTTP-Version CRLF
    def create_request_line(self, method_type, url, version):
        return '{} {} {}\n\n'.format(method_type, url, version)

    def tcp_send(self, host, port, message):
        tcpsoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcpsoc.connect((host, port))
        tcpsoc.sendall(message.encode())
        response = tcpsoc.recv(4096)
        tcpsoc.close()
        return response


if __name__ == '__main__':
    HttpConnection()






