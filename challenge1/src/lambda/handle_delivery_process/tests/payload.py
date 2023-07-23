import json

RECEIPT_HANDLE = "receipt"

DB_ORDER_STATUS_CANCELLED = {
    "pkey": "ORD0000005",
    "Item": "test_item",
    "Status": "CANCELLED",
    "Description": "Description for item_test",
    "Amount": 100,
    "OrderedBy": "dummy@dummy.com",
}

SQS_ORDER_BODY = {
    "pkey": "ORD0000005",
    "Item": "test_item",
    "Status": "PLACED",
    "Description": "Description for item_test",
    "Amount": 100,
    "OrderedBy": "dummy@dummy.com",
}

SQS_QUEUE_SENDS_MESSAGE = {
    "Messages": [
        {
            "ReceiptHandle": RECEIPT_HANDLE,
            "Body": json.dumps(SQS_ORDER_BODY),
        }
    ]
}
