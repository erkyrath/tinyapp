import sys
import argparse
import importlib.util
import importlib.machinery

import werkzeug.serving
from werkzeug.middleware.shared_data import SharedDataMiddleware

parser = argparse.ArgumentParser()

parser.add_argument('filename')
parser.add_argument('-u', '--uri', dest='uri')
parser.add_argument('-d', '--dir', dest='dir')

args = parser.parse_args()

### https://werkzeug.palletsprojects.com/en/stable/middleware/shared_data/

def application(environ, start_response):
    print('###', environ.get('PATH_INFO', '???'))
    
    request_uri = environ.get('REQUEST_URI', '???')
    status = '404 Not Found'
    msg = '###Not found: %s' % (request_uri,)
    output = status + '\n\n' + msg
    boutput = output.encode()
    content_type = 'text/plain; charset=utf-8'
    
    response_headers = [
        ('Content-Type', content_type),
        ('Content-Length', str(len(boutput)))
    ]
    start_response(status, response_headers)
    yield boutput

loader = importlib.machinery.SourceFileLoader('_wsgiapp', args.filename)
spec = importlib.util.spec_from_loader('_wsgiapp', loader=loader)
appmod = importlib.util.module_from_spec(spec)
sys.modules['_wsgiapp'] = appmod
spec.loader.exec_module(appmod)

if args.dir:
    application = SharedDataMiddleware(application, { '/': args.dir })

werkzeug.serving.run_simple('localhost', 8001, application)

