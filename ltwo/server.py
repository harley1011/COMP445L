import sys
import getopt
import lib.detailedusage as detailedusage
import lib.https as https


def main(argv):
    request = {}

    # parse options
    try:
        opts, args = getopt.getopt(argv, "v:p:d:", ['v=', 'p=', 'd='])
    except getopt.GetoptError:
        give_help()

    request['verbose'] = False
    request['port'] = 8000
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
    http_server = https.HTTPServer()
    http_server.run_server('', request['port'], request['verbose'])



main(sys.argv[1:])

