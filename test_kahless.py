import pytest

from kahless.api import Api


def test_basic_route_adding(api):
    @api.route("/home")
    def home(req, resp):
        resp.text = "yolo"


def test_duplicate_route(api):
    @api.route("/home")
    def home(req, resp):
        resp.text = "yolo"

    with pytest.raises(AssertionError):

        @api.route("/home")
        def home2(req, resp):
            resp.text = "yolo"


def test_client_can_send_requests(api, client):
    response_text = "THIS IS COOL"

    @api.route("/hey")
    def cool(req, resp):
        resp.text = response_text

    assert client.get("http://testserver/hey").text == response_text


def test_parametrized_route(api, client):
    @api.route("/{name}")
    def hello(req, resp, name):
        resp.text = f"hey {name}"

    assert client.get("http://testserver/matthew").text == "hey matthew"
    assert client.get("http://testserver/ashley").text == "hey ashley"


def test_404_response(client):
    response = client.get("http://testserver/bogus")
    assert response.status_code == 404
    assert response.text == "Not found"


def test_cbv_get(api, client):
    response_text = "this is a get request"

    @api.route("/book")
    class BookResource:
        def get(self, req, resp):
            resp.text = response_text

    assert client.get("http://testserver/book").text == response_text


def test_cbv_post(api, client):
    response_text = "this is a post request"

    @api.route("/book")
    class BookResource:
        def post(self, req, resp):
            resp.text = response_text

    assert client.post("http://testserver/book").text == response_text


def test_cbv_wrong_method(api, client):
    @api.route("/book")
    class BookResource:
        def post(self, req, resp):
            resp.text = "yolo"

    with pytest.raises(AttributeError):
        assert client.get("http://testserver/book")


def test_alternative_route(api, client):
    response_text = "Alternative way to add a route"

    def home(req, resp):
        resp.text = response_text

    api.add_route("/alternative", home)
    assert client.get("http://testserver/alternative").text == response_text


def test_template(api, client):
    @api.route("/html")
    def html_handler(req, resp):
        resp.body = api.template(
            "index.html", context={"title": "Some Title", "name": "Some Name"}
        ).encode()

    response = client.get("http://testserver/html")

    assert "text/html" in response.headers["Content-Type"]
    assert "Some Title" in response.text
    assert "Some Name" in response.text


def test_custom_exception_handler(api, client):
    def on_exception(req, resp, exc):
        resp.text = "AttributeErrorHappened"

    api.add_exception_handler(on_exception)

    @api.route("/")
    def index(req, resp):
        raise AttributeError()

    response = client.get("http://testserver/")

    assert response.text == "AttributeErrorHappened"


FILE_DIR = "css"
FILE_NAME = "main.css"
FILE_CONTENTS = "body {background-color: red}"


def _create_static(static_dir):
    asset = static_dir.mkdir(FILE_DIR).join(FILE_NAME)
    asset.write(FILE_CONTENTS)

    return asset


def test_assets_are_served(tmpdir_factory):
    static_dir = tmpdir_factory.mktemp("static")
    _create_static(static_dir)
    api = Api(static_dir=str(static_dir))
    client = api.test_session()

    response = client.get(f"http://testserver/static/{FILE_DIR}/{FILE_NAME}")

    assert response.status_code == 200
    assert response.text == FILE_CONTENTS


def test_404_is_returned_for_nonexistent_static_file(client):
    assert client.get(f"http://testserver/static/main.css)").status_code == 404


def test_json_response_helper(api, client):
    @api.route("/json")
    def json_handler(req, resp):
        resp.json = {"name": "bubmo"}

    response = client.get("http://testserver/json")
    json_body = response.json()

    assert response.headers["Content-Type"] == "application/json"
    assert json_body["name"] == "bubmo"


def test_html_response_helper(api, client):
    @api.route("/html")
    def html_handler(req, resp):
        resp.html = api.template(
            "index.html", context={"title": "Best Title", "name": "Best Name"}
        )

    response = client.get("http://testserver/html")

    assert "text/html" in response.headers["Content-Type"]
    assert "Best Title" in response.text
    assert "Best Name" in response.text


def test_text_response_helper(api, client):
    response_text = "Just Plain Text"

    @api.route("/text")
    def text_handler(req, resp):
        resp.text = response_text

    response = client.get("http://testserver/text")

    assert "text/plain" in response.headers["Content-Type"]
    assert response.text == response_text


def test_manually_setting_body(api, client):
    @api.route("/body")
    def text_handler(req, resp):
        resp.body = b"Byte Body"
        resp.content_type = "text/plain"

    response = client.get("http://testserver/body")
    assert "text/plain" in response.headers["Content-Type"]
    assert response.text == "Byte Body"
