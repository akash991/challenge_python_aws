from unittest.mock import patch, Mock
from pytest import fixture

get_requests = []

def __get_response_mock(*args, **kargs):
    return get_requests.pop(0)

@fixture(autouse=True)
def mock_get_requests():
    with patch("content.index.requests.get", side_effect=__get_response_mock):
        yield
    assert len(get_requests) == 0

@fixture(autouse=True)
def mock_get_access_token():
    with patch("content.index.get_access_token") as accsess_token:
        accsess_token.return_value = ""
        yield accsess_token

class utils:
    def set_get_requests_response(response_list):
        global get_requests
        get_requests = [Mock(text=i, status_code=j) for i, j in response_list]

