import os.path
import html

from werkzeug.exceptions import NotFound
from werkzeug.middleware.shared_data import SharedDataMiddleware

class StaticFileMiddleware:
    def __init__(self, app, appuri, dirtree):
        self.app = app
        self.appuri = appuri
        self.appurislash = '/' if appuri == '/' else appuri+'/'
        self.dirtree = dirtree
        self.fileapp = SharedDataMiddleware(NotFound('URL not found'), { '/': dirtree })

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        if path == self.appuri or path.startswith(self.appurislash):
            return self.app(environ, start_response)
        if path.startswith('/'):
            path = path[ 1 : ]
        realpath = os.path.join(self.dirtree, path)
        if os.path.isdir(realpath):
            if path != '' and not path.endswith('/'):
                return self.redirectdir('/'+path+'/', environ, start_response)
            if path.endswith('/'):
                pathindex = path + 'index.html'
            else:
                pathindex = path + '/index.html'
            realpathindex = os.path.join(self.dirtree, pathindex)
            if os.path.isfile(realpathindex):
                environ['PATH_INFO'] = '/'+pathindex
                return self.fileapp(environ, start_response)
            else:
                return self.dirlisting(realpath, environ, start_response)
        return self.fileapp(environ, start_response)

    def redirectdir(self, newuri, environ, start_response):
        response_headers = [
            ('Location', newuri),
            ('Content-Length', '0'),
        ]
        start_response('301 Moved Permanently', response_headers)
        yield b''
    
    def dirlisting(self, realpath, environ, start_response):
        output = DIRTEMPLATE
        val = environ.get('PATH_INFO', '')
        output = output.replace('$PATH$', html.escape(val))
        boutput = output.encode()
        response_headers = [
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Content-Length', str(len(boutput)))
        ]
        start_response('200 OK', response_headers)
        yield boutput

DIRTEMPLATE = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Directory $PATH$</title>
</head>
<body>
<h1>Directory $PATH$</h1>
<ul>
$FILES$
</ul>
</body>
</html>'''
