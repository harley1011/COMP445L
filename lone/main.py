import sys
import getopt
import re

DETAILED_USAGE = '''
httpc is a curl-like application but supports HTTP protocol only.

Usage: httpc command [arguments]

The commands are:
get             Executes a HTTP GET request and prints the response.
post            Executes a HTTP POST request and prints the response.
help            Prints this screen.

Use "httpc help [command]" for more information about a command.
'''

DETAILED_USAGE_GET = '''
Usage: httpc get [-v] [-h key:value] URL

Get executes a HTTP GET request for a given URL.
-v              Prints the detail of the response such as protocol, status and headers.
-h key:value    Associates headers to HTTP Request with the format 'key:value'.
'''

DETAILED_USAGE_POST = '''
Usage: httpc post [-v] [-h key:value] [-d inline-data] [-f file] URL

Post executes a HTTP POST request for a given URL with inline data or from file.
-v              Prints the detail of the response such as protocol, status and headers.
-h key:value    Associates headers to HTTP Request with the format 'key:value'.
-d string       Associates an inline data to the body HTTP POST request.
-f file         Associates the content of a file to the body HTTP POST request.

Either [-d] or [-f] can be used, but not both.
'''


def main(argv):
    """
    Creates a request object containing all the required parameters to form a GET or POST HTTP request.

    The format of the GET request object is as follows:

    {
        'type': 'GET',
        'url': 'www.google.com',
        'header':
            {
                'key1': 'value1',
                'key2': 'value2'
            },
        'verbose': True
    }

    The format of the POST request object is as follows:

    {
        'type': 'POST',
        'url': 'www.google.com',
        'header':
            {
                'key1': 'value1',
                'key2': 'value2'
            },
        'verbose': True,
        'data': {
            'type': 'inline',  # [inline] or [file]
            'value': 'test'
        }
    }
    """

    # create request object
    request = {}

    # check request
    if len(argv) == 0:
        give_help()
    elif argv[0].lower() == 'get':
        request['type'] = 'GET'
    elif argv[0].lower() == 'post':
        request['type'] = 'POST'
    elif argv[0].lower() == 'help':
        if len(argv) > 1 and (argv[1].lower() == 'get' or argv[1].lower() == 'post'):
            give_help_request(argv[1].lower())
        else:
            give_help()

    argv = argv[1:]

    # parse options
    try:
        opts, args = getopt.getopt(argv, "vh:d:f:")
    except getopt.GetoptError:
        give_help()

    request['verbose'] = False
    request['header'] = {}

    if request['type'] == 'POST':
        request['data'] = {
            'type': None,  # [inline] or [file]
            'value': None
        }

    count = len(argv)

    # cycle through options
    for opt, arg in opts:
        # verbose request
        if opt == '-v':
            request['verbose'] = True
            count -= 1
        # header data
        elif opt == '-h':
            header_d = get_header_data(arg)
            if header_d is not None:
                request['header'][header_d['key']] = header_d['value']
            else:
                print('-h accepts an argument of format "key:value"')
                sys.exit()
            count -= 2
        # inline data (POST request only)
        elif opt == '-d':
            if request['data']['value'] is not None:
                print('Cannot use options -d and -f at the same time')
                sys.exit()
            elif request['type'] == 'GET':
                print('Cannot use options -d with a GET request')
                sys.exit()
            request['data']['type'] = 'inline'
            request['data']['value'] = arg
            count -= 2
        # file data (POST request only)
        elif opt == '-f':
            if request['data']['value'] is not None:
                print ('Cannot use options -d and -f at the same time')
                sys.exit()
            elif request['type'] == 'GET':
                print('Cannot use options -d with a GET request')
                sys.exit()
            request['data']['type'] = 'file'
            request['data']['value'] = arg
            count -= 2

    # check if a URL is provided
    if count != 1:
        print ('No URL was provided')
        sys.exit()

    request['url'] = argv[-1]


def give_help():
    print(DETAILED_USAGE)
    sys.exit()


def give_help_request(type):
    if type == 'get':
        print(DETAILED_USAGE_GET)
    elif type == 'post':
        print(DETAILED_USAGE_POST)
    sys.exit()


def get_header_data(data):
    match_obj = re.match(r'(.*):(.*)?', data, re.M|re.I)

    if match_obj:
        key_value = {}
        key_value['key'] = match_obj.group(1)
        key_value['value'] = match_obj.group(2)
        return key_value
    else:
        return None


main(sys.argv[1:])
