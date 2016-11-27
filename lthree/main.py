import getopt
import json
import re
import sys
import threading

from urllib.parse import urlparse

import lib.clientdetailedusage as detailedusage
import lib.httpc as httpc


def main(argv):
    # create request object
    request = {}

    # check request
    request['type'] = get_request_type(argv)

    argv = argv[1:]

    # parse options
    try:
        opts, args = getopt.getopt(argv, "vrh:c:d:f:", ['d=', 'f='])
    except getopt.GetoptError:
        give_help()

    request['verbose'] = False
    request['redirect'] = False
    request['concurrent_request_no'] = 1
    request['header'] = {}

    if request['type'] == 'POST':
        request['data'] = {
            'type': None,  # [inline] or [file]
            'value': None
        }
    else:
        request['data'] = None

    count = len(argv)

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
        elif opt == '-r' or opt == '--r':
            request['redirect'] = True
            count -= 1
        elif opt == '-c' or opt == '--c':
            request['concurrent_request_no'] = int(arg)
            count -= 2

    # check if a URL is provided
    if count != 1:
        print ('No URL was provided')
        sys.exit()

    request['url'] = argv[-1]

    if request['concurrent_request_no'] > 1:
        threads =[]
        for i in range(0, request['concurrent_request_no']):
            t = threading.Thread(target=send_http, args=(request,), daemon=True)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()
    else:
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
    if not request['url'].startswith('http'):
        request['url'] = '%s%s' % ('http://', request['url'])

    url_parse = urlparse(request['url'])
    http_connection = httpc.HttpConnection(url_parse.netloc, 80, output=request['verbose'])

    path = url_parse.path
    if request['type'] == 'GET':
        if len(url_parse.query) > 0:
            path = '{}?{}'.format(url_parse.path, url_parse.query)

    request['header']['Agent'] = 'http-client'

    if request['data'] is None:
        http_connection.request(request['type'], path, headers=request['header'])
    else:
        http_connection.request(request['type'], path, request['data']['value'], headers=request['header'])
    result = http_connection.getresponse()

    if request['redirect'] and result.status_code == 302:
        if 'Location' not in result.headers:
            print('No redirect location found in response header')
            print(result.body)
            return

        location = result.headers['Location']
        if request['verbose']:
            print('Redirect enabled, redirecting to {0}'.format(location))
        request['url'] = location
        send_http(request)
    else:
        print(result.body)


def print_request(request):
    output = {}
    output['url'] = request['url']
    output['headers'] = request['header']

    s = '\n'
    s += json.dumps(output, indent=4, sort_keys=True)
    s += '\n'

    print(s)


main(sys.argv[1:])
