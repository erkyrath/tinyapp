from tinyapp.app import TinyApp
from tinyapp.handler import ReqHandler
from tinyapp.constants import PLAINTEXT

"""
TinyApp example which just handles a couple of URLs. See README.md.
"""

class han_Home(ReqHandler):
    def do_get(self, req):
        yield '<html><body>This is an HTML response.</body></html>\n'

class han_File(ReqHandler):
    def do_get(self, req):
        req.set_content_type(PLAINTEXT)
        yield 'This is a text file...\n'
        yield 'Which is yielded on two lines.\n'

appinstance = TinyApp([
    ('', han_Home),
    ('/file', han_File),
])

application = appinstance.application
