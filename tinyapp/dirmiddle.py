import os.path
import html

from werkzeug.exceptions import NotFound
from werkzeug.middleware.shared_data import SharedDataMiddleware

class StaticFileMiddleware:
    def __init__(self, app, appuri, appurislash, dirtree):
        self.app = app
        self.appuri = appuri
        self.appurislash = appurislash
        self.dirtree = dirtree
        self.fileapp = SharedDataMiddleware(NotFound('URL not found'), { '/': dirtree })

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        if path == self.appuri or path.startswith(self.appurislash):
            return self.app(environ, start_response)
        if path.startswith('/'):
            path = path[ 1 : ]
        realpath = os.path.join(self.dirtree, path)
        print('### path', path, realpath)
        if os.path.isdir(realpath):
            ### redir 301 for the non-slashed case?
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
    def dirlisting(self, realpath, environ, start_response):
        output = self.DIRTEMPLATE
        val = environ.get('PATH_INFO', '')
        output = output.replace('$PATH$', html.escape(val))
        boutput = output.encode()
        response_headers = [
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Content-Length', str(len(boutput)))
        ]
        start_response('200 OK', response_headers)
        yield boutput

