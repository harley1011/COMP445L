import sys
import re
import getopt
import queue
import json
import threading
import datetime
from os import listdir
from os.path import isfile, join
import lib.detailedusage as detailedusage
import lib.https as https

server_options = {}
request_queue = queue.Queue()
http_server = https.HTTPServer(request_queue)
request_thread = None

def main(argv):
    if argv[0].lower() == 'help':
        give_help()

    # parse options
    try:
        opts, args = getopt.getopt(argv, "vp:d:", ['v=', 'p=', 'd='])
    except getopt.GetoptError:
        give_help()

    server_options['verbose'] = False
    server_options['port'] = 80
    server_options['directory'] = './'

    # cycle through options
    for opt, arg in opts:
        # verbose request
        if opt == '-v':
            server_options['verbose'] = True
        elif opt == '-p' or opt == '--p':
            server_options['port'] = int(arg)
        elif opt == '-d' or opt == '--d':
            server_options['directory'] = arg

    threading.Thread(target=handle_requests, args=(request_queue, server_options['directory']), daemon=True).start()

    threading.Thread(target=http_server.run_server, args=('127.0.0.1', server_options['port'], server_options['verbose']), daemon=True).start()

    while True:
        choice = input()
        if choice == "q":
            http_server.stop_server()
            sys.exit()


def give_help():
    detailedusage.get_usage()
    sys.exit()


def handle_requests(request_queue, directory):
    while True:
        request = request_queue.get()

        handle_request(request, directory)


def handle_request(request, directory):
    if request.method == 'GET' and request.path == '/':
        response = directory_list(request, directory)
    elif request.method == 'GET':
        response = file_content(request, directory)
    elif request.method == 'POST':
        response = file_set_content(request, directory)
    else:
        response = handle_error(request, directory)

    request.reply_to_request(response.response_header, response.response_body, server_options['verbose'])


def directory_list(request, directory):
    # get directory list
    files = []
    for file in listdir(directory):
        if isfile(join(directory, file)):
            files.append(file)

    # make body
    response_body = json.dumps(files)

    # make header
    type_line = '{} {} {}\r\n'.format(request.http_version, '200', 'OK')
    content_type = 'Content-Type: {}'.format('application/json')

    return create_response(type_line, content_type, response_body)


def file_content(request, directory):
    if not valid_path(request.path):
        return handle_file_error(request, directory)

    d = directory
    if d.endswith('/'):
        d = d[:-1]

    try:
        with open(d + request.path, 'rb') as content_file:
            content = content_file.read()
    except IOError:
        return handle_file_error(request, directory)

    # make body
    response_body = content

    # make header
    type_line = '{} {} {}\r\n'.format(request.http_version, '200', 'OK')
    content_type = 'Content-Type: {}'.format(get_file_type(request.path))

    return create_response(type_line, content_type, response_body)


def file_set_content(request, directory):
    if not valid_path(request.path):
        return handle_file_error(request, directory)

    d = directory
    if d.endswith('/'):
        d = d[:-1]

    try:
        file = open(d + request.path, 'wb')
    except IOError:
        return handle_file_error(request, directory)

    file.write(request.message_body.encode())

    # make body
    response_body = 'SUCCESS'

    # make header
    type_line = '{} {} {}\r\n'.format(request.http_version, '200', 'OK')
    content_type = 'Content-Type: {}'.format('text/plain')

    return create_response(type_line, content_type, response_body)


def handle_error(request, directory):
    # make body
    response_body = 'Not A File'

    # make header
    type_line = '{} {} {}\r\n'.format(request.http_version, '400', 'Bad Request')
    content_type = 'Content-Type: {}'.format('text/plain')

    return create_response(type_line, content_type, response_body)


def handle_file_error(request, directory):
    # make body
    response_body = 'Not A File'

    # make header
    type_line = '{} {} {}\r\n'.format(request.http_version, '404', 'Not Found')
    content_type = 'Content-Type: {}'.format('text/plain')

    return create_response(type_line, content_type, response_body)


def create_response(type_line, content_type, response_body):
    response_header = '{}Server: {}\r\n'.format(type_line, 'COMP 445 HTTP Server')

    now = datetime.datetime.now()
    response_header = '{}Date: {}\r\n'.format(response_header, str(now))

    response_header = '{}{}\r\n'.format(response_header, content_type)
    response_header = '{}Content-Length: {}\r\n'.format(response_header, len(response_body))
    response_header = '{}Connection: {}\r\n'.format(response_header, 'Close')
    response_header = '{}Access-Control-Allow-Origin: {}\r\n'.format(response_header, '*')
    response_header = '{}Access-Control-Allow-Credentials: {}\r\n'.format(response_header, 'true')

    # make response
    response_header = '{}\r\n'.format(response_header)
    return https.HttpResponse(response_header, response_body)


def valid_path(path):
    return re.match(r'^/[^\./]+\.\w+$', path, re.M|re.I) is not None


def get_file_type(path):
    match_object = re.match(r'^/[^\./]+\.(\w+)$', path, re.M|re.I)

    type = match_object.group(1)

    if type == 'json':
        return 'application/json'
    elif type == 'pdf':
        return 'application/pdf'
    elif type == 'html':
        return 'text/html'
    elif type == 'png':
        return 'image/png'
    elif type == 'jpg' or type == 'jpeg':
        return 'image/jpg'
    elif type == 'bmp':
        return 'image/bmp'
    elif type == 'gif':
        return 'image/gif'
    else:
        return 'application/octet-stream'




main(sys.argv[1:])

