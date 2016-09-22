import sys
import getopt

DETAILED_USAGE = 'httpc (get|post) [-v] (-h "k:v")* [-d inline-data] [-f file] URL'
DETAILED_USAGE_GET = 'httpc (get|post) [-v] (-h "k:v")* [-d inline-data] [-f file] URL'
DETAILED_USAGE_POST = 'httpc (get|post) [-v] (-h "k:v")* [-d inline-data] [-f file] URL'


def main(argv):

    request_type = None

    #check action
    if len(argv) == 0:
        give_help()
    elif argv[0] == 'get':
        request_type = 'GET'
    elif argv[0] == 'post':
        request_type = 'POST'
    elif argv[0] == 'help':
        if len(argv) > 1 and (argv[1] == 'get' or argv[1] == 'post'):
            give_help_type(argv[1])
        else:
            give_help()

    argv = argv[1:]

    try:
        opts, args = getopt.getopt(argv, "vh:d:f:")
    except getopt.GetoptError:
        give_help()

    isVerbose = False
    headers = {}
    data = None

    for opt, arg in opts:
        if opt == '-v':
            isVerbose = True
        elif opt == '-h':
            print('Option H')
        elif opt == '-d':
            if data is not None:
                print('Cannot use options -d and -f at the same time')
                sys.exit()
            data = arg
        elif opt == '-f':
            if data is not None:
                print ('Cannot use options -d and -f at the same time')
                sys.exit()
            data = arg

    print(data)


def give_help():
    print(DETAILED_USAGE)
    sys.exit()


def give_help_type(type):
    if type == 'get':
        print(DETAILED_USAGE_GET)
    elif type == 'post':
        print(DETAILED_USAGE_POST)
    sys.exit()


main(sys.argv[1:])
