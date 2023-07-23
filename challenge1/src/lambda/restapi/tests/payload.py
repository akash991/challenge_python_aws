TABLENAME = "TEST_TABLE"
POST_ORDER_INPUT_JSON = {"Item": "dummy", "Amount": 100}

DB_PUT_ITEM_EXPECTED_PARAMS = {
    "Amount": 100,
    "Item": "dummy",
    "OrderedBy": "dummy@dummy.com",
    "Status": "PROCESSING",
    "pkey": "ORD0000001",
}

DB_GET_ITEM_ORDER_DETAILS = DB_PUT_ITEM_EXPECTED_PARAMS

POST_ORDER_INPUT_JSON_INVALID = {"Item": "dummy", "Amount": "100"}
