import sys
import getopt
import queue
import threading
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
    request['directory'] = ''

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
    threading.Thread(target=handle_requests, args=(request_queue, ), daemon=True).start()

    http_server = https.HTTPServer(request_queue)
    http_server.run_server('127.0.0.1', request['port'], request['verbose'])


def handle_requests(request_queue):
    while True:
        request = request_queue.get()
        print('Method:', request.method)
        print('Path:', request.path)
        print('HTTP Version:', request.http_version)
        print('Headers:', request.headers)
        print('Body:', request.message_body)


main(sys.argv[1:])

