from tinyapp.app import TinyApp
from tinyapp.handler import ReqHandler
from tinyapp.constants import PLAINTEXT, HTML

class han_Home(ReqHandler):
    def do_get(self, req):
        req.set_content_type(PLAINTEXT)
        yield 'Basic example.\n'

class han_Test(ReqHandler):
    def do_get(self, req):
        yield '<html><body>This is an HTML response.</body></html>\n'

appinstance = TinyApp([
    ('', han_Home),
    ('/test', han_Test),
])
application = appinstance.application

