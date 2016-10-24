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
                elif data.find(b'\r\n\r\n') != -1:
                    # If we have this then we know we have the status line and all the headers
                    request.extend(data)

                    http_request = HttpRequest()

                    more_content = http_request.parse_request(request, conn)
                    if not more_content:
                        break
                else:
                    request.extend(data)
                    more_content = http_request.add_content(request)
                    if not more_content:
                        break
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
        self.raw_request = None
        self.request_index = 0

    def parse_request(self, request, connection):
        # extract stuff from response
        # see http response for how we parsed the response

        self.connection = connection

        self.raw_request = request
        self.request_index = len(request)
        request = request.split(b'\r\n\r\n', 1)
        request_header = request[0].decode('utf-8').split('\r\n', 1)
        request_body = request[1]

        status_line = request_header.pop(0).split(' ')
        request_header = request_header[0].split('\r\n')
        self.method = status_line[0]
        self.path = status_line[1]
        self.http_version = status_line[2]

        while len(request_header) > 0:
            header = request_header.pop(0)

            if header == '':
                break

            header = header.split(": ", 1)
            self.headers[header[0]] = header[1]

        try:
            decode_type = 'utf-8'
            if 'Content-Type' in self.headers and 'charset=' in self.headers['Content-Type']:
                decode_type = self.headers['Content-Type'].split('charset=')[1]
            self.message_body += request_body.decode(decode_type)
        except:
            self.message_body += request_body

        if 'Content-Length' in self.headers:
            return len(self.message_body) < int(self.headers['Content-Length'])

        return False

    def add_content(self, request):
        body = request[self.request_index:]
        self.request_index = len(request)
        try:
            decode_type = 'utf-8'
            if 'Content-Type' in self.headers and 'charset=' in self.headers['Content-Type']:
                decode_type = self.headers['Content-Type'].split('charset=')[1]
            self.message_body += body.decode(decode_type)
        except:
            self.message_body += body

        return self.headers['Content-Length'] == len(self.message_body)
