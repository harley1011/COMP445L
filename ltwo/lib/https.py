import socket
import threading


class HTTPServer(object):
    def run_server(self, host, port):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.bind((host, port))
            listener.listen(5)
            print('Echo server is listening at', port)
            while True:
                conn, addr = listener.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr)).start()
        finally:
            listener.close()

    @staticmethod
    def handle_client(conn, addr):
        print('New client from', addr)
        request = bytearray()
        try:
            while True:
                data = conn.recv(4096)
                more_content = False
                if not data:
                    break
                elif data.find("\r\n\r\n"):
                    # If we have this then we know we have the status line and all the headers
                    request.extend(data)
                    http_request = HttpRequest()

                    more_content = http_request.parse_request(request)
                    if more_content:
                        break
                else:
                    request.extend(data)

        finally:
            conn.close()
            return http_request


class HttpRequest(object):
    def __init__(self):
        self.method = 'GET'
        self.path = '/'
        self.http_version = "HTTP/1.0"
        self.headers = {}
        self.message_body = ''

    def parse_request(self, request):
        # extract stuff from response
        # see http response for how we parsed the response
        self.method = 'GET'

        return False

    def add_content(self, request):
        self.message_body += request

        return self.headers['Content-Length'] == len(self.message_body)
