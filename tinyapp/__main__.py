import sys
import argparse
import importlib.util
import importlib.machinery

import werkzeug.serving
import werkzeug.exceptions
from werkzeug.middleware.shared_data import SharedDataMiddleware

parser = argparse.ArgumentParser()

parser.add_argument('filename')
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
    print('### path_info: %r' % (path_info,))

    new_path_info = None
    if appuri == '/':
        if path_info == appuri:
            new_path_info = ''
        else:
            new_path_info = path_info
    else:
        if path_info == appuri:
            new_path_info = ''
        elif path_info.startswith(appuri+'/'):
            new_path_info = path_info[ len(appuri) : ]

    if new_path_info is not None:
        print('### ...match, new path_info: %r' % (new_path_info,))
        environ['PATH_INFO'] = new_path_info
        return appmod.application(environ, start_response)

    request_uri = environ.get('REQUEST_URI', '???')
    notfound = werkzeug.exceptions.NotFound('URL not found: ' + request_uri)
    return notfound(environ, start_response)

loader = importlib.machinery.SourceFileLoader('_wsgiapp', args.filename)
spec = importlib.util.spec_from_loader('_wsgiapp', loader=loader)
appmod = importlib.util.module_from_spec(spec)
sys.modules['_wsgiapp'] = appmod
spec.loader.exec_module(appmod)

static_files = None
if args.dir:
    static_files = { '/': args.dir }

werkzeug.serving.run_simple('localhost', 8001, application, use_reloader=True, static_files=static_files)

