import pytest

from kahless.api import Api


@pytest.fixture
def api():
    return Api()


@pytest.fixture
def client(api):
    return api.test_session()
