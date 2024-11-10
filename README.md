# TinyApp: a minimal WSGI app framework

- Designed by Andrew Plotkin <erkyrath@eblong.com>

This is a very simple framework for building web apps in Python.

If you're thinking about using this, you probably want to go use [Flask][] instead. TinyApp does the same thing as Flask, only less complete, less elegant, and unsupported.

[Flask]: https://flask.palletsprojects.com/

I only wrote TinyApp because I wanted to learn how WSGI worked. Now I do! And now I've used it in two projects (which could have been Flask but aren't). So I might as well break TinyApp out into its own library and document it at least a little.

TinyApp supports Python 3.7 and later. That's really old, but one of those projects I mentioned is on an old server with Py 3.7, so I'm stuck with it.

## A minimal application

This is a very simple TinyApp application (see `example/minimal.wsgi`):

```
from tinyapp.app import TinyApp
from tinyapp.handler import ReqHandler
from tinyapp.constants import PLAINTEXT

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

application = appinstance.application
```

The `application` global is WSGI's entry point.

## Testing on the command line

To run the application:

```
$ python -m tinyapp example/minimal.wsgi
```

This runs your application in a [werkzeug development server][werkzeug]. Load the URL `http://localhost:8001` to see the `han_Home` response. Or load `http://localhost:8001/file` to see the `han_File` response.

You can also supply `--port` and `--host` arguments, as is traditional for miniservers. To make your application visible outside the local machine, use `--host 0.0.0.0`.

This is only for testing! Like the docs say:

[werkzeug]: https://werkzeug.palletsprojects.com/en/stable/serving/

> Do not use the development server when deploying to production. It is intended for use only during local development. It is not designed to be particularly efficient, stable, or secure.

On the up side, if you edit your application or any module that it imports, werkzeug will automatically reload the changes.

A more usual setup looks like this:

```
$ python -m tinyapp example/minimal.wsgi --uri /app --dir staticpath
```

This mimics the way you would install the app under Apache. `http://localhost:8001/app` is routed to your app, as are all URLs under that (e.g. `http://localhost:8001/app/file`). All *other* URLs are served as [static files][SharedData] out of the `staticpath` directory.

(The `--dir` argument does _not_ load `index.html` or directory listings for directory paths. So in this mode, the root `http://localhost:8001/` URL will always return a 404.)

[SharedData]: https://werkzeug.palletsprojects.com/en/stable/middleware/shared_data/

## Installing on Apache

This is the normal mode of TinyApp in production.

This isn't a step-by-step recipe, but the basics are:

- Install the `mod-wsgi` module:

```
pip3 install mod-wsgi
```

- Update your Apache `httpd.conf` file to load the module:

```
LoadModule wsgi_module /path/to/mod_wsgi.so
WSGIScriptAlias /app /path/to/app.wsgi
WSGIPythonPath /path/to/libdir
```

Note that `/app` is the root URI that your app will use (like the `--uri /app` argument above). The `libdir` is a directory containing the modules your app will import, and also `tinyapp` itself (if that isn't in your system Python path).

- Restart Apache to pick up the changes.

