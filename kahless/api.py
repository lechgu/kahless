import inspect
import os

import jinja2
import requests
import wsgiadapter
from parse import parse
from webob import Request
from whitenoise import WhiteNoise

from kahless.middleware import Middleware
from kahless.response import Response


class Api:
    def __init__(self, templates_dir="templates", static_dir="static"):
        self.routes = {}
        self.templates_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.abspath(templates_dir))
        )
        self.exception_handler = None
        self.whitenoise = WhiteNoise(self.wsgi_app, root=static_dir)
        self.middleware = Middleware(self)

    def __call__(self, environ, start_response):
        path_info = environ["PATH_INFO"]
        if path_info.startswith("/static"):
            environ["PATH_INFO"] = path_info[len("/static") :]  # noqa
            return self.whitenoise(environ, start_response)
        return self.middleware(environ, start_response)

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.handle_request(request)
        return response(environ, start_response)

    def route(self, path, allowed_methods=None):
        def wrapper(handler):
            self.add_route(path, handler, allowed_methods)

        return wrapper

    def add_route(self, path, handler, allowed_methods=None):
        if not allowed_methods:
            allowed_methods = [
                "get",
                "post",
                "put",
                "patch",
                "delete",
                "options",
            ]
        assert path not in self.routes
        self.routes[path] = dict(
            handler=handler, allowed_methods=allowed_methods
        )

    def template(self, template_name, context=None):
        if not context:
            context = {}
        return self.templates_env.get_template(template_name).render(**context)

    def find_handler(self, request_path):
        for path, handler_data in self.routes.items():
            pres = parse(path, request_path)
            if pres:
                return handler_data, pres.named
        return None, None

    def default_response(self, request, response):
        response.status_code = 404
        response.text = "Not found"

    def handle_request(self, request):
        response = Response()
        handler_data, kwargs = self.find_handler(request.path)
        try:
            if handler_data:
                handler = handler_data["handler"]
                allowed_methods = handler_data["allowed_methods"]
                if inspect.isclass(handler):
                    handler = getattr(handler(), request.method.lower(), None)
                    if not handler:
                        raise AttributeError(
                            "Method not allowed", request.method
                        )
                else:
                    if request.method.lower() not in allowed_methods:
                        raise AttributeError(
                            "Method not allowed", request.method
                        )
                handler(request, response, **kwargs)
            else:
                self.default_response(request, response)
        except Exception as e:
            if self.exception_handler:
                self.exception_handler(request, response, e)
            else:
                raise e
        return response

    def add_exception_handler(self, exception_handler):
        self.exception_handler = exception_handler

    def add_middleware(self, middleware_cls):
        self.middleware.add(middleware_cls)

    def test_session(self, base_url="http://testserver"):
        session = requests.Session()
        session.mount(prefix=base_url, adapter=wsgiadapter.WSGIAdapter(self))
        return session
