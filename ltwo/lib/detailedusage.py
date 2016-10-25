import sys

DETAILED_USAGE = '''
httpfs is a simple file server.

usage: httpfs [-v] [-p PORT] [-d PATH-TO-DIR]

-v              Prints debugging messages.
-p              Specifies the port number that the server will listen and serve at. Default is 8080.
-d              Specifies the directory that the server will use to read/write requested files.
                Default is the current directory when launching the application.
'''


def get_usage():
    print(DETAILED_USAGE)
    sys.exit()