import re
import html

from tinyapp.app import TinyApp, TinyRequest
from tinyapp.handler import ReqHandler
from tinyapp.handler import before, beforeall
from tinyapp.excepts import HTTPError, HTTPRedirectPost

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
    if 'loggedinas' in req.cookies:
        req._username = req.cookies['loggedinas'].value
    return han(req)

def checkloggedin(req, han):
    if not req._username:
        raise HTTPError('401 Unauthorized', 'Not logged in')
    return han(req)

class han_Home(ReqHandler):
    def do_get(self, req):
        if req._username:
            tem = StinjaTemplate(home_template)
            yield tem.render(username=req._username)
        else:
            tem = StinjaTemplate(login_template)
            yield tem.render()

    def do_post(self, req):
        username = req.get_input_field('name')
        password = req.get_input_field('password')
        if not username or not password:
            tem = StinjaTemplate(login_template)
            yield tem.render(username=username, formerror='Please enter username and password.')
            return

        if password != 'swordfish':
            tem = StinjaTemplate(login_template)
            yield tem.render(username=username, formerror='Incorrect password. Hint: the password is "swordfish".')
            return

        req.set_cookie('loggedinas', username)
        raise HTTPRedirectPost('/')

class han_Logout(ReqHandler):
    def do_get(self, req):
        req.set_cookie('loggedinas', '', maxage=0)
        raise HTTPRedirectPost('/')

@beforeall(checkloggedin)
class han_Content(ReqHandler):
    def do_get(self, req):
        tem = StinjaTemplate(content_template)
        yield tem.render()
        

class AuthDemoRequest(TinyRequest):
    """Our app-specific subclass of TinyRequest. This just has a spot
    to stash the current username.
    """
    def __init__(self, app, env):
        TinyRequest.__init__(self, app, env)
        self._username = None

class AuthDemoApp(TinyApp):
    def __init__(self):
        handlers = [
            ('', han_Home),
            ('/logout', han_Logout),
            ('/content', han_Content),
        ]
        TinyApp.__init__(self, handlers, wrapall = [ findusercookie ])

    def create_request(self, environ):
        return AuthDemoRequest(self, environ)

appinstance = AuthDemoApp()

application = appinstance.application
