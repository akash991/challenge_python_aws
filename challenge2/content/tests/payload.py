import json

METADATA_STRUCTURE = {
    "key1": "val1",
    "key2": {
        "key3": "val3",
        "key4": "val4",
    },
}


class GetMetadataFull:
    func_arg = None
    request_get_respose = (
        ("key1\nkey2/", 200),
        ("val1", 200),
        ("key3\nkey4", 200),
        ("val3", 200),
        ("val4", 200),
    )
    expected_response = json.dumps(METADATA_STRUCTURE)


class GetMetadataStrVal:
    func_args = "key1"
    request_get_respose = (("val1", 200),)
    expected_response = "val1"


class GetMetadataDictVal:
    func_args = "key2/"
    request_get_respose = (
        ("key3\nkey4", 200),
        ("val3", 200),
        ("val4", 200),
    )
    expected_response = json.dumps({"key3": "val3", "key4": "val4"})
