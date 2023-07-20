import pytest
from unittest.mock import patch
from content.get_item import parse

dataset_response_only_str = [
    pytest.param({"a":"b"}, "a", "b", id="flat_object_valid_path_only_str"),
    pytest.param({"a":{"b":{"c":"d"}}}, "a/b/c", "d", id="nested_object_valid_path_only_str"),
    pytest.param({"a":{"b":{"c":"d"}}}, "a/d/c", None, id="nested_object_invalid_path_only_str"),
    pytest.param({"a":{"b":{"c":"d"}}}, "a/b", None, id="nested_object_response_not_str_only_str"),
    pytest.param({"a":{"b":{"c":"d"}}}, "", None, id="nested_object_empty_path_only_str"),
]

@pytest.mark.parametrize("object, key, expected_res", dataset_response_only_str)
def test_get_item_parse_only_str_true(object, key, expected_res):
    response = parse(object, key)
    assert response == expected_res


dataset_response_str_or_dict = [
    pytest.param({"a":"b"}, "a", "b", id="flat_object_valid_path"),
    pytest.param({"a":{"b":{"c":"d"}}}, "a/b/c", "d", id="nested_object_valid_path"),
    pytest.param({"a":{"b":{"c":"d"}}}, "a/d/c", None, id="nested_object_invalid_path"),
    pytest.param({"a":{"b":{"c":"d"}}}, "a/b", {"c":"d"}, id="nested_object_response_not_str"),
    pytest.param({"a":{"b":{"c":"d"}}}, "", None, id="nested_object_empty_path"),
]

@pytest.mark.parametrize("object, key, expected_res", dataset_response_str_or_dict)
def test_get_item_parse_only_str_false(object, key, expected_res):
    response = parse(object, key, False)
    assert response == expected_res