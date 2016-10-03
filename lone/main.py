import sys
import getopt
import re
import lib.detailedusage as detailedusage
import lib.httpc as httpc
import json
from urllib.parse import urlparse


def main(argv):

    # create request object
    request = {}

    # check request
    request['type'] = get_request_type(argv)

    argv = argv[1:]

    # parse options
    try:
        opts, args = getopt.getopt(argv, "vh:d:f:", ['d=', 'f='])
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

    print(opts)

    # cycle through options
    for opt, arg in opts:
        # verbose request
        if opt == '-v':
            request['verbose'] = True
            count -= 1
        # header data
        elif opt == '-h':
            get_header_data(request, arg)
            count -= 2
        # inline data (POST request only)
        elif opt == '-d' or opt == '--d':
            get_inline_data(request, arg)
            count -= 2
        # file data (POST request only)
        elif opt == '-f' or opt == '--f':
            get_file_data(request, arg)
            count -= 2

    # check if a URL is provided
    if count != 1:
        print ('No URL was provided')
        sys.exit()

    request['url'] = argv[-1]

    send_http(request)


def get_request_type(argv):
    if len(argv) == 0:
        give_help()
    elif argv[0].lower() == 'get':
        return 'GET'
    elif argv[0].lower() == 'post':
        return 'POST'
    elif argv[0].lower() == 'help':
        if len(argv) > 1 and (argv[1].lower() == 'get' or argv[1].lower() == 'post'):
            give_help_request(argv[1].lower())
        else:
            give_help()


def give_help():
    detailedusage.get_usage()
    sys.exit()


def give_help_request(type):
    detailedusage.get_usage_request(type)
    sys.exit()


def get_header_data(request, data):
    match_obj = re.match(r'(.*):(.*)?', data, re.M|re.I)

    header_d = None
    if match_obj:
        key_value = {}
        key_value['key'] = match_obj.group(1)
        key_value['value'] = match_obj.group(2)
        header_d =  key_value

    if header_d is not None:
        request['header'][header_d['key']] = header_d['value']
    else:
        print('-h accepts an argument of format "key:value"')
        sys.exit()


def get_inline_data(request, arg):
    if request['data']['value'] is not None:
        print('Cannot use options -d and -f at the same time')
        sys.exit()
    elif request['type'] == 'GET':
        print('Cannot use options -d with a GET request')
        sys.exit()
    request['data']['type'] = 'inline'
    request['data']['value'] = arg


def get_file_data(request, arg):
    if request['data']['value'] is not None:
        print ('Cannot use options -d and -f at the same time')
        sys.exit()
    elif request['type'] == 'GET':
        print('Cannot use options -d with a GET request')
        sys.exit()
    request['data']['type'] = 'file'

    f = open(arg, 'r')
    body = f.read()

    request['data']['value'] = body


def send_http(request):
    print(request)

    if not request['url'].startswith('http'):
        request['url'] = '%s%s' % ('http://', request['url'])

    url_parse = urlparse(request['url'])

    http_connection = httpc.HttpConnection(url_parse.netloc, 80)

    print_request(request)

    if request['data'] is not None:
        http_connection.request(request['type'], url_parse.path, request['data']['value'])
    else:
        http_connection.request(request['type'], url_parse.path)
    result = http_connection.getresponse()

    if request['verbose']:
        print(result.raw_response)


def print_request(request):
    output = {}

    output['url'] = request['url']
    output['headers'] = request['header']

    s = '\n'
    s += json.dumps(output, indent=4, sort_keys=True)
    s += '\n'

    print(s)


main(sys.argv[1:])
