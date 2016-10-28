import sys
import getopt
import queue
import threading
import datetime
from os import listdir
from os.path import isfile, join
import lib.detailedusage as detailedusage
import lib.https as https


def main(argv):
    request = {}

    if argv[0].lower() == 'help':
        give_help()

    # parse options
    try:
        opts, args = getopt.getopt(argv, "vp:d:", ['v=', 'p=', 'd='])
    except getopt.GetoptError:
        give_help()

    request['verbose'] = False
    request['port'] = 8080
    request['directory'] = './'

    # cycle through options
    for opt, arg in opts:
        # verbose request
        if opt == '-v':
            request['verbose'] = True
        elif opt == '-p' or opt == '--p':
            request['port'] = int(arg)
        elif opt == '-d' or opt == '--d':
            request['directory'] = arg

    start_server(request)


def give_help():
    detailedusage.get_usage()
    sys.exit()


def start_server(request):
    request_queue = queue.Queue()
    threading.Thread(target=handle_requests, args=(request_queue, request['directory']), daemon=True).start()

    http_server = https.HTTPServer(request_queue)
    http_server.run_server('127.0.0.1', request['port'], request['verbose'])


def handle_requests(request_queue, directory):
    while True:
        request = request_queue.get()

        handle_request(request, directory)


def handle_request(request, directory):
    response = None
    if request.method == 'GET' and request.path == '/':
        response = directory_list(request, directory)
    elif request.method == 'GET':
        response = file_content(request, directory)
    elif request.method == 'POST':
        response = file_set_content(request, directory)
    else:
        response = handle_error(request, directory)

    print(response)


def directory_list(request, directory):
    files = []
    for file in listdir(directory):
        if isfile(join(directory, file)):
            files.append(file)

    # make body
    response_body = str(files)

    # make header
    type_line = '{} {} {}\r\n'.format(request.http_version, '200', 'OK')
    content_type = 'Content-Type: {}'.format('application/json')

    return create_response(type_line, content_type, response_body)


def file_content(request, directory):
    # make body
    response_body = directory

    # make header
    type_line = '{} {} {}\r\n'.format(request.http_version, '200', 'OK')
    content_type = 'Content-Type: {}'.format('text/plain')

    return create_response(type_line, content_type, response_body)


def file_set_content(request, directory):
    # make body
    response_body = directory

    # make header
    type_line = '{} {} {}\r\n'.format(request.http_version, '200', 'OK')
    content_type = 'Content-Type: {}'.format('text/plain')

    return create_response(type_line, content_type, response_body)


def handle_error(request, directory):
    # make body
    response_body = directory

    # make header
    type_line = '{} {} {}\r\n'.format(request.http_version, '400', 'Bad Request')
    content_type = 'Content-Type: {}'.format('text/plain')

    return create_response(type_line, content_type, response_body)


def create_response(type_line, content_type, response_body):
    response_header = '{}Server: {}\r\n'.format(type_line, 'COMP 445 HTTP Server')

    now = datetime.datetime.now()
    response_header = '{}Date: {}\r\n'.format(response_header, str(now))

    # response_header = '{}Content-Type: {}\r\n'.format(response_header, 'text/plain')
    response_header = '{}{}\r\n'.format(response_header, content_type)
    response_header = '{}Content-Length: {}\r\n'.format(response_header, len(response_body))
    response_header = '{}Connection: {}\r\n'.format(response_header, 'Close')
    response_header = '{}Access-Control-Allow-Origin: {}\r\n'.format(response_header, '*')
    response_header = '{}Access-Control-Allow-Credentials: {}\r\n'.format(response_header, 'true')

    # make response
    response = '{}\r\n{}'.format(response_header, response_body)

    return response


main(sys.argv[1:])

