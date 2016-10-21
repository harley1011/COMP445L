import sys
import getopt
import lib.detailedusage as detailedusage
import lib.https as https

def main(argv):
    # create request object
    request = {}

    argv = argv[1:]

    # parse options
    try:
        opts, args = getopt.getopt(argv, "v:p:d:", ['p=', 'd='])
    except getopt.GetoptError:
        give_help()

    request['verbose'] = False
    request['port'] = ''
    request['directory'] = ''

    count = len(argv)

    # cycle through options
    for opt, arg in opts:
        # verbose request
        if opt == '-v':
            request['verbose'] = True
            count -= 1
        elif opt == '-p' or opt == '--p':
            request['port'] = arg
            count -= 2
        # file data (POST request only)
        elif opt == '-d' or opt == '--d':
            request['directory'] = arg
            count -= 2
    # check if a URL is provided
    if count != 1:
        print ('No URL was provided')
        sys.exit()

    request['url'] = argv[-1]

    start_server(request)


def give_help():
    detailedusage.get_usage()
    sys.exit()


def start_server(request):
    if request['verbose']:
        print('Starting server on port {}'.format(request['port']))
    print('hello');
    http_server = https.HTTPServer()





