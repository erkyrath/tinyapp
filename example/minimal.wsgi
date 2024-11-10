from tinyapp.app import TinyApp
from tinyapp.handler import ReqHandler
from tinyapp.constants import PLAINTEXT

"""
TinyApp example which just handles a couple of URLs. See README.md.
"""

# Define two handlers.

class han_Home(ReqHandler):
    def do_get(self, req):
        yield '<html><body>This is an HTML response.</body></html>\n'

class han_File(ReqHandler):
    def do_get(self, req):
        req.set_content_type(PLAINTEXT)
        yield 'This is a text file...\n'
        yield 'Which is yielded on two lines.\n'

# Create the TinyApp instance, mapping a URI to each of the above handlers.

appinstance = TinyApp([
    ('', han_Home),
    ('/file', han_File),
])

# Define the module "application" global, which is WSGI's entry point.

application = appinstance.application
