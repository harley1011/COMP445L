import getopt
import json
import re
import sys
import threading
from os import listdir
from os.path import isfile, join
import lib.detailedusage as detailedusage
import lib.https as https

import queue

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
        threading.Thread(target=handle_request,args=(request, directory), daemon=True).start()


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

    return https.HttpResponse(request.http_version, '200', 'OK', 'application/json', json.dumps(files))


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

    return https.HttpResponse(request.http_version, '200', 'OK', get_file_type(request.path), content)


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

    return https.HttpResponse(request.http_version, '200', 'OK', 'text/plain', 'SUCCESS')


def handle_error(request, directory):
    return https.HttpResponse(request.http_version, '400', 'Bad Request', 'text/plain', 'Not A File')


def handle_file_error(request, directory):
    return https.HttpResponse(request.http_version, '404', 'Not Found', 'text/plain', 'Not A File')


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


if __name__ == "__main__":
    main(sys.argv[1:])


