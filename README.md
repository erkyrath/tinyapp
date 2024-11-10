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

## Running the thing

### Testing on the command line

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

### Installing on Apache

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

### Installing on other servers

WSGI is supposed to be a universal glue, so TinyApp should work in anything. See [werkzeug's list of production servers][prodserv]. I've only tested Apache though.

[prodserv]: https://werkzeug.palletsprojects.com/en/stable/deployment/

## A quick tour of TinyApp

When an HTTP request comes in, TinyApp constructs a `TinyRequest` object (wrapping the request). It then looks through your list of handlers for one which matches the request. If it finds one, it calls `handler.do_get(req)`, `handler.do_post(req)`, or `handler.do_head(req)` as appropriate. Override one or more of these methods to do your web stuff.

(There is a default implementation of `do_head(req)` which just calls `do_get(req)` and then returns the headers with no data. This is usually good enough.)

### Your basic handler

The simplest thing your handler can do is yield one or more strings.

```
class han_Home(ReqHandler):
    def do_get(self, req):
        yield '<html><body>This is an HTML response.</body></html>\n'
```

By default, the `Content-Type` is HTML. You can alter this by calling `set_content_type()`. (Before you start yielding, please.) A few handy Content-Type values are defined in `tinyapp.constants`.

```
from tinyapp.constants import PLAINTEXT

class han_File(ReqHandler):
    def do_get(self, req):
        req.set_content_type(PLAINTEXT)
        yield 'This is a text file...\n'
```

Your handler can raise `HTTPError` (from `tinyapp.excepts`) to generate an HTTP error result.

```
from tinyapp.excepts import HTTPError

class han_File(ReqHandler):
    def do_get(self, req):
        raise HTTPError('404 Not Found', 'File not found')
```

If you want to return binary data, raise `HTTPRawResponse`. In this case you must construct the list of headers (including `Content-Length`!) and also supply an iterator that yields some number of `bytes` objects.

```
from tinyapp.excepts import HTTPRawResponse

class han_File(ReqHandler):
    def do_get(self, req):
        # ... construct headerlist and iterbytes
        raise HTTPRawResponse('200 OK', headerlist, iterbytes)
```

### What to do with a request

The TinyRequest has a few useful attributes:

- `req.app`: A reference to the TinyApp.
- `req.env`: The WSGI environment that generated the request.
- `req.request_method`: `"GET"`, `"POST"`, or `"HEAD"`.
- `req.path_info`: The URI relative to your app. (That is, the app's URI prefix has been removed.)
- `req.match`: The regexp match object from matching the request URI. See "Matches", below.
- `req.query`: A dict which represents the query string of the request (the `?key=value` part of the URL).
- `req.input`: A dict which represents the POST data of the request, if any.
- `req.cookies`: A [SimpleCookies][httpcookies] object representing the incoming cookies.

(Note that `req.query` and `req.input` both take the form of a dict mapping keys to _lists_ of values. See [urllib.parse.parse_qs()][parse_qs].

[parse_qs]: https://docs.python.org/3/library/urllib.parse.html#urllib.parse.parse_qs

TinyRequest methods:

- `req.get_query_field(key, default=None)`: Get one field in the query string of the request (the `?key=value` part of the URL).
- `req.get_input_field(key, default=None)`: Get one field from the POST data of the request.
- `req.set_status(val)`: Set the response HTTP status (like `"200 OK"`).
- `req.set_content_type(val)`: Set the response HTTP `Content-Type` header.
- `req.set_cookie(key, val, path='/', httponly=False, maxage=None)`: Set an outgoing cookie via header. (See [http.cookies][httpcookies].)
- `req.add_header(key, val)`: Add an arbitrary header.

[httpcookies]: https://docs.python.org/3/library/http.cookies.html

### Request matches

In your list of handlers:

```
appinstance = TinyApp([
    ('', han_Home),
    ('/file', han_File),
])
```

...the URI part of the tuple is really a regular expression. (It's always a complete match, with `$` assumed at the end.)

This lets you do some neat tricks. The regexp can include groups:

```
    ('/item/(?P<category>[^/]+)/(?P<item>[^/]+)', han_SelectItem),
```

Here a request like `/item/cheese/stilton` generates a [Match][rematch] object with two named groups: `category` and `item`. The Match is available as `req.match`, so you could examine `req.match.group('category')`, for example.

[rematch]: https://docs.python.org/3/library/re.html#re.Match

### Handler wrappers

A handler wrapper is a function that looks at a request and either

- throws an exception, or
- handles the request, or
- passes it on, perhaps adding info first.

For example, you might write a wrapper function to load user account data based on cookies. Then another wrapper for a particular resource could check that account data and throw a 401 if the account is not authorized.

A wrapper is simply a function that looks like:

```
def wrapperfunc(req, han):
    # perhaps yield a response and then return
    # perhaps throw an HTTPError
    # perhaps modify req
    # pass the request down the chain...
    return han(req)
```

To apply a wrapper to a `do_get()` or `do_post()` method in a ReqHandler:

```
class han_Home(ReqHandler):
    @before(wrapperfunc)
    def do_get(self, req):
        yield '<html><body>This is an HTML response.</body></html>\n'
```

To apply a wrapper to *both* the `do_get()` or `do_post()` methods in a ReqHandler:

```
@beforeall(wrapperfunc)
class han_Home(ReqHandler):
    def do_get(self, req):
        yield '<html><body>This is an HTML response.</body></html>\n'
```

To apply wrappers to *every* method in every ReqHandler in your app, pass a `wrapall` list to the TinyApp constructor:

```
appinstance = TinyApp([
    ('', han_Home),
], wrapall = [ wrapperfunc ])
```

By the way, if you want to add functionality to the TinyRequest class, you can create a derived class and then override the `app.create_request()` factory function.

