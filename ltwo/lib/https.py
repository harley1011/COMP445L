import socket
import threading


class HTTPServer(object):
    def __init__(self):
        self.verbose = False

    def run_server(self, host, port, verbose):
        self.verbose = verbose
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.bind((host, port))
            listener.listen(5)
            if self.verbose:
                print('Server is listening on port ', port)
            while True:
                conn, addr = listener.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr)).start()
        finally:
            listener.close()

    def handle_client(self, conn, addr):
        if self.verbose:
            print('New client from ', addr)

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
            return http_request
        except:
            conn.close()
            return None

    @staticmethod
    def handle_response_to_client(http_request):
        http_request.connection.sendall('response here')
        http_request.connection.close()


class HttpRequest(object):
    def __init__(self):
        self.method = 'GET'
        self.path = '/'
        self.http_version = "HTTP/1.0"
        self.headers = {}
        self.message_body = ''
        self.connection = None

    def parse_request(self, request, connection):
        # extract stuff from response
        # see http response for how we parsed the response
        self.method = 'GET'
        self.connection = connection
        return False

    def add_content(self, request):
        self.message_body += request

        return self.headers['Content-Length'] == len(self.message_body)
