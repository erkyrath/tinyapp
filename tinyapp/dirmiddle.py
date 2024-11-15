import os.path
import html
import urllib.parse

from werkzeug.exceptions import NotFound
from werkzeug.middleware.shared_data import SharedDataMiddleware

# This module imports werkzeug, but it is only used by __main__
# (which also imports werkzeug).

class StaticFileMiddleware:
    """A WSGI application component to serve a directory tree of
    static files.

    This uses werkzeug's SharedDataMiddleware component to serve
    the files themselves. It adds the capability to serve the
    *directories*, either by finding "index.html" or generating
    a directory listing.
    """
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
        ls = []
        for ent in os.scandir(realpath):
            name = ent.name
            if ent.is_dir():
                name = name + '/'
            ls.append('<li><a href="%s">%s</a>\n' % (urllib.parse.quote(name), html.escape(name),))
        ls.sort(key=lambda val:val.lower())
        output = DIRTEMPLATE
        val = environ.get('PATH_INFO', '')
        output = output.replace('$PATH$', html.escape(val))
        output = output.replace('$FILES$', ''.join(ls))
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
