import socket
from urllib.parse import urlparse


class HttpConnection(object):
    def __init__(self, host, version):
        self.connection_info = urlparse(host)
        self.http_version = version

    def post(self):
        self.request_line('POST', self.connection_info.path, self.http_version)

    def get(self):
        request = self.request_line('GET',self.connection_info.path, self.http_version)
        response = self.tcp_send('www.' + self.connection_info.netloc,80, request)
        print(response)

    # Request-Line   = Method SP Request-URI SP HTTP-Version CRLF
    def request_line(self, method_type, url, version):
        return '{} {} {}\n\n'.format(method_type, url, version)

    def tcp_send(self, host, port, message):
        tcpsoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcpsoc.connect((host, port))
        tcpsoc.sendall(message.encode())
        response = tcpsoc.recv(4096)
        tcpsoc.close()
        return str(response)


if __name__ == '__main__':
    HttpConnection()






