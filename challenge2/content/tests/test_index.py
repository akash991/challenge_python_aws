import json
from conftest import utils
from content.index import get_metadata

METADATA_STRUCTURE = {
    "key1": "val1",
    "key2": {
        "key3": "val3",
        "key4": "val4",
    },
}


def test_get_metadata_prints_complete_data():
    """
    unit test to fetch full instance data
    """
    utils.set_get_requests_response(
        (
            ("key1\nkey2/", 200),
            ("val1", 200),
            ("key3\nkey4", 200),
            ("val3", 200),
            ("val4", 200),
        )
    )
    response = get_metadata()
    assert json.loads(response) == METADATA_STRUCTURE


def test_get_metadata_input_key_to_str_value():
    """
    unit test to fetch value of the provided path
    """
    utils.set_get_requests_response((("val1", 200),))
    response = get_metadata("key1")
    assert response == "val1"


def test_get_metadata_input_key_to_dict_value():
    """
    unit test to fetch value of a dictionary
    """
    utils.set_get_requests_response(
        (
            ("key3\nkey4", 200),
            ("val3", 200),
            ("val4", 200),
        )
    )
    response = get_metadata("key2/")
    assert json.loads(response) == {
        "key3": "val3",
        "key4": "val4",
    }


def test_get_metadata_invalid_key_path():
    """
    test to verify -ve scenarios
    """
    utils.set_get_requests_response(
        (
            ("key3\nkey4", 200),
            ("", 404),
        )
    )
    response = get_metadata("key2/")
    assert response == None
