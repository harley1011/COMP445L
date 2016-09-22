import sys

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


def get_usage():
    print(DETAILED_USAGE)
    sys.exit()


def get_usage_request(type):
    if type == 'get':
        print(DETAILED_USAGE_GET)
    elif type == 'post':
        print(DETAILED_USAGE_POST)
