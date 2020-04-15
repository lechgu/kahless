import json

import webob


class Response:
    def __init__(self):
        self.json = None
        self.html = None
        self.text = None
        self.content_type = None
        self.status_code = 200

    def __call__(self, environ, start_response):
        self.set_body_and_content_type()
        resp = webob.Response(
            body=self.body,
            content_type=self.content_type,
            status=self.status_code,
        )
        return resp(environ, start_response)

    def set_body_and_content_type(self):
        if self.json:
            self.body = json.dumps(self.json).encode()
            self.content_type = "application/json"
        if self.html:
            self.body = self.html.encode()
            self.content_type = "text/html"
        if self.text:
            self.body = self.text
            self.content_type = "text/plain"
