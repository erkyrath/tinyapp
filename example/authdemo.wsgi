import re
import html

from tinyapp.app import TinyApp, TinyRequest
from tinyapp.handler import ReqHandler
from tinyapp.handler import before, beforeall
from tinyapp.excepts import HTTPError, HTTPRedirectPost

"""
###

To run:
    python -m tinyapp example/authdemo.wsgi
"""

class StinjaTemplate:
    """An incredibly minimal HTML templating system. I use Jinja2 in
    real projects -- Jinja2 is great -- but I didn't want the dependency
    for this demo, so here's a sliver of a replacement.
    """
    def __init__(self, template):
        self.template = template

    def render(self, **args):
        def func(match):
            val = args.get(match.group(1))
            if val is None:
                return ''
            return html.escape(str(val), quote=True)
        res = re.sub(r'\{\{([^}]+)\}\}', func, self.template)
        return res

# HTML templates for the demo.

login_template = '''
<html><body>
<form method="post" action="/">
<div>
<input class="FormInput" autocapitalize="off"
  id="login_field" name="name" type="text" value="{{username}}" placeholder="Username"
  autofocus="autofocus">
</div>
<div>
<input class="FormInput" autocomplete="disabled"
  id="password_field" name="password" type="password" placeholder="Password">
</div>
<div>
<input class="FormButton" name="commit" type="submit" value="Sign in">
</div>
<p>{{formerror}}</p>
</form>
<p><a href="/content">View the secret content</a></p>
</body></html>
'''

home_template = '''
<html><body>
<p>Welcome. You are logged in as {{username}}.</p>
<p><a href="/content">View the secret content</a></p>
<p><a href="/logout">Log out</a></p>
</body></html>
'''

content_template = '''
<html><body>
<p>This is the secret content, which you can only see if you're logged in.</p>
<p><a href="/logout">Log out</a></p>
</body></html>
'''

def findusercookie(req, han):
    """
    Wrapper which checks the request cookies for the "loggedinas"
    key, which indicates that the user is logged in.
    This is applied to all requests.
    """
    if 'loggedinas' in req.cookies:
        # Store the username in the request object. Note that req
        # is an AuthDemoRequest, our subclass of TinyRequest which
        # adds the _username field.
        req._username = req.cookies['loggedinas'].value
    return han(req)

def checkloggedin(req, han):
    """
    Wrapper which checks to make sure the user is logged in. If not,
    throws an HTTP error.
    This is applied to the /content handler.
    """
    if not req._username:
        raise HTTPError('401 Unauthorized', 'Not logged in')
    return han(req)

# Our handlers:

class han_Home(ReqHandler):
    def do_get(self, req):
        # On GET, we display either the home screen or the login
        # screen, depending on whether the user is logged in.
        #
        # Remember that the findusercookie() wrapper has already run,
        # so req._username will be set for logged-in users.
        
        if req._username:
            tem = StinjaTemplate(home_template)
            yield tem.render(username=req._username)
        else:
            tem = StinjaTemplate(login_template)
            yield tem.render()

    def do_post(self, req):
        # On POST, we check the form fields.
        username = req.get_input_field('name')
        password = req.get_input_field('password')
        
        if not username or not password:
            # No good. We re-render the login screen, showing an error.
            # We set username so that {{username}} will be filled in
            # nicely on the login form.
            tem = StinjaTemplate(login_template)
            yield tem.render(username=username, formerror='Please enter username and password.')
            return

        if password != 'swordfish':
            # Again, no good.
            tem = StinjaTemplate(login_template)
            yield tem.render(username=username, formerror='Incorrect password. Hint: the password is "swordfish".')
            return

        # Good! Set a cookie to indicate this for future requests.
        req.set_cookie('loggedinas', username)
        
        # The HTTPRedirectPost exception does a 303 redirect to the
        # given URI. The cookie we just set is included with the
        # redirect.
        raise HTTPRedirectPost('/')

class han_Logout(ReqHandler):
    def do_get(self, req):
        # Wipe the cookie.
        req.set_cookie('loggedinas', '', maxage=0)
        raise HTTPRedirectPost('/')

@beforeall(checkloggedin)
class han_Content(ReqHandler):
    def do_get(self, req):
        # Display the secret content.
        # The checkloggedin() wrapper has already run; it threw an
        # exception if the user was not logged in.
        tem = StinjaTemplate(content_template)
        yield tem.render()
        

class AuthDemoRequest(TinyRequest):
    """Our app-specific subclass of TinyRequest. This just has a spot
    to stash the current username. If this is set (and nonempty),
    the user is logged in. See findusercookie().
    """
    def __init__(self, app, env):
        TinyRequest.__init__(self, app, env)
        self._username = None

class AuthDemoApp(TinyApp):
    """Our app-specific subclass of TinyApp. It's tidier to wrap up
    all the initializer info in here.
    """
    def __init__(self):
        # Initialize TinyApp with our handlers and a universal
        # wrapper.
        
        handlers = [
            ('', han_Home),
            ('/logout', han_Logout),
            ('/content', han_Content),
        ]
        TinyApp.__init__(self, handlers, wrapall = [ findusercookie ])

    def create_request(self, environ):
        # Return our app-specific subclass of TinyRequest.
        return AuthDemoRequest(self, environ)

# Create the TinyApp instance. The handler list will be set up in
# our initializer.

appinstance = AuthDemoApp()

# Define the module "application" global, which is WSGI's entry point.

application = appinstance.application
