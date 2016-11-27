import threading
import datetime
import lib.tcp as tcp

class HTTPServer(object):
    def __init__(self, queue):
        self.verbose = False
        self.queue = queue
        self.listener = None

    def run_server(self, host, port, verbose):
        self.verbose = verbose
        try:
            self.listener = tcp.Tcp(host, 3000)
            self.listener.start_listening(port)
            if self.verbose:
                print('Server is listening on port', port)
            while True:
                conn, addr = self.listener.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr, self.queue)).start()

        finally:
            self.listener.close()

    def stop_server(self):
        self.listener.close()

    def handle_client(self, conn, addr, queue):
        if self.verbose:
            print('New client from ', addr)

        request = bytearray()
        try:
            while True:
                data = conn.recv_from(4096)
                if not data:
                    break
                elif data.find(b'\r\n\r\n') != -1:
                    # If we have this then we know we have the status line and all the headers
                    request.extend(data)
                    http_request = HttpRequest()
                    http_request.request_addr = addr
                    more_content = http_request.parse_request(request, conn)
                    if not more_content:
                        break
                else:
                    request.extend(data)
                    more_content = http_request.add_content(request)
                    if not more_content:
                        break
            queue.put(http_request)
        except:
            conn.close()

    @staticmethod
    def handle_response_to_client(http_request):
        http_request.connection.send('localhost', http_request.connection.peer_port, 'response here')
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
        self.request_addr = None

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

    def reply_to_request(self, header, body, verbose):
        self.connection.send('localhost', self.connection.peer_port, header.encode())
        try:
            send_body = body.encode()
        except:
            send_body = body
        if verbose:
            print('\r\nSending response to client ', self.request_addr)
            print(header)
            print(send_body)
            # sleep(random.randrange(10))
            print('\r\nClosing connection to client {} now...'.format(self.request_addr))

        self.connection.send('localhost', self.connection.peer_port, send_body)
        self.connection.close()


class HttpResponse(object):
        def __init__(self, http_version, status_code, message, content_type, response_body):
            type_line = '{} {} {}\r\n'.format(http_version, status_code, message)
            content_type = 'Content-Type: {}'.format(content_type)

            response_header = '{}Server: {}\r\n'.format(type_line, 'COMP 445 HTTP Server')

            now = datetime.datetime.now()
            response_header = '{}Date: {}\r\n'.format(response_header, str(now))

            response_header = '{}{}\r\n'.format(response_header, content_type)
            response_header = '{}Content-Length: {}\r\n'.format(response_header, len(response_body))
            response_header = '{}Connection: {}\r\n'.format(response_header, 'Close')
            response_header = '{}Access-Control-Allow-Origin: {}\r\n'.format(response_header, '*')
            response_header = '{}Access-Control-Allow-Credentials: {}\r\n'.format(response_header, 'true')

            self.response_header = '{}\r\n'.format(response_header)
            self.response_body = response_body



