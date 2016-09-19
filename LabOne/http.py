import socket

def post (url, port):
    print(url)

def get (url, port):
    print(url)

# Request-Line   = Method SP Request-URI SP HTTP-Version CRLF
def request_line(method_type, url, version):
    return '/{} {} {} \r\n'.format(method_type, url, version)
    
def tcpSend (host, port, message):
    tcpsoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpsoc.bind((host, port))
    tcpsoc.send(message)
    response = tcpsoc.recv()


