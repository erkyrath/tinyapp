import sys
import os

from tinyapp.app import TinyApp
from tinyapp.handler import ReqHandler
from tinyapp.constants import PLAINTEXT

"""
TinyApp example which displays all the request info in plain text.
Handy for debugging or exploring how TinyApp works.
"""

class han_Home(ReqHandler):
    def do_get(self, req):
        req.set_content_type(PLAINTEXT)
        yield 'sys.version: %s\n' % (sys.version,)
        yield 'sys.path: %s\n' % (sys.path,)
        yield '__name__: %s\n' % (__name__,)
        if req.match:
            yield 'match: %s\n' % (req.match,)
            yield 'match.groups: %s\n' % (req.match.groups(),)
            yield 'match.groupdict: %s\n' % (req.match.groupdict(),)
        yield 'getpid=%s\n' % (os.getpid(),)
        yield 'getuid=%s, geteuid=%s, getgid=%s, getegid=%s\n' % (os.getuid(), os.geteuid(), os.getgid(), os.getegid(),)
        yield 'environ:\n'
        for key, val in sorted(req.env.items()):
            yield '  %s: %s\n' % (key, val,)
        if req.query:
            yield 'query: %s\n' % (req.query,)
        if 'wsgi.input' in req.env:
            val = req.env['wsgi.input'].read()
            yield 'input: %s\n' % (val,)

    def do_post(self, req):
        return self.do_get(req)

appinstance = TinyApp([
    ('', han_Home),
    ('/(?P<arg>.*)', han_Home),
])

application = appinstance.application

