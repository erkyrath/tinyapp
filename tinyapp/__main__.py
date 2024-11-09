import sys
import argparse
import importlib.util
import importlib.machinery

import werkzeug.serving
import werkzeug.exceptions
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.wsgi import get_input_stream

"""
Wrapper to run a tinyapp application in a server process. To run:

    python -m tinyapp APP.WSGI

This uses the werkzeug development server. Like the docs say:

> Do not use the development server when deploying to production. It
> is intended for use only during local development. It is not
> designed to be particularly efficient, stable, or secure.
"""

parser = argparse.ArgumentParser()

parser.add_argument('filename')
parser.add_argument('--host', dest='host', default='localhost')
parser.add_argument('-p', '--port', dest='port', type=int, default=8001)
parser.add_argument('-u', '--uri', dest='uri')
parser.add_argument('-d', '--dir', dest='dir')

args = parser.parse_args()

if not args.uri:
    appuri = '/'
else:
    appuri = args.uri
    if not appuri.startswith('/'):
        appuri = '/' + appuri

def application(environ, start_response):
    path_info = environ.get('PATH_INFO', '')

    # The way we handle the PATH_INFO variable is a bit finicky. It is
    # meant to replicate how Apache/mod_wsgi works.
    
    new_path_info = None
    if path_info == appuri:
        new_path_info = ''
    else:
        if appuri == '/':
            new_path_info = path_info
        elif path_info.startswith(appuri+'/'):
            new_path_info = path_info[ len(appuri) : ]

    if new_path_info is not None:
        environ['PATH_INFO'] = new_path_info
        if 'wsgi.input' in environ:
            environ['wsgi.input'] = get_input_stream(environ)
        return appmod.application(environ, start_response)

    request_uri = environ.get('REQUEST_URI', '???')
    notfound = werkzeug.exceptions.NotFound('URL not found: ' + request_uri)
    return notfound(environ, start_response)

# Import the app file as a Python module. We have to use SourceFileLoader
# because the file suffix might not be ".py".
# The module name doesn't matter, so we just call it "_wsgiapp".

loader = importlib.machinery.SourceFileLoader('_wsgiapp', args.filename)
spec = importlib.util.spec_from_loader('_wsgiapp', loader=loader)
appmod = importlib.util.module_from_spec(spec)
sys.modules['_wsgiapp'] = appmod
spec.loader.exec_module(appmod)

# Launch the werkzeug server.

static_files = None
if args.dir:
    static_files = { '/': args.dir }

werkzeug.serving.run_simple(args.host, args.port, application, use_reloader=True, static_files=static_files)

