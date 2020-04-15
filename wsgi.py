from kahless.api import Api

app = Api()


@app.route("/home")
def home(request, response):
    response.text = "Home"


@app.route("/about")
def about(request, response):
    response.text = "About"


@app.route("/hello/{name}")
def greeting(request, response, name):
    response.text = f"Hello, {name}"


@app.route("/book")
class BookResource:
    def get(self, req, resp):
        resp.text = "Books page"

    def post(self, req, resp):
        resp.text = "Endpoint to create a book"


@app.route("/template")
def template_handler(req, resp):
    resp.html = app.template(
        "index.html", context={"name": "kahless", "title": "Best Framework"}
    )


@app.route("/json")
def json_handler(req, resp):
    resp.json = {"name": "data", "type": "JSON"}


@app.route("/text")
def text_handler(req, resp):
    resp.text = "This is a simple text"
