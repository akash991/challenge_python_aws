from .conftest import utils
from .payload import (
    RECEIPT_HANDLE,
    SQS_ORDER_BODY,
    SQS_QUEUE_SENDS_MESSAGE,
    DB_ORDER_STATUS_CANCELLED
)
from botocore.stub import Stubber
from handle_delivery_process.index import handler


def test_no_message_in_the_queue(sqs_client_stub: Stubber):
    """
    No new orde placed in the queue
    """
    sqs_client_stub.add_response(
        method="receive_message",
        service_response={},
    )
    handler({}, None)


def test_sqs_queue_contains_cancelled_order(sqs_client_stub: Stubber, ddb_client_stub: Stubber):
    """
    sqs queue contains order which was cancelled 
    before it was processed by the lambda
    """
    # stub receive_message call 
    sqs_client_stub.add_response(
        method="receive_message",
        service_response=SQS_QUEUE_SENDS_MESSAGE,
    )
    # check order status in db
    ddb_client_stub.add_response(
        method="get_item",
        expected_params={
            "Key": {"pkey": SQS_ORDER_BODY["pkey"]},
            "TableName": "TEST_TABLE",
        },
        # order got CANCELLED before it was moved to IN_TRANSIT
        service_response={"Item": utils.serialize_py_to_db(DB_ORDER_STATUS_CANCELLED)},
    )
    # delete message from SQS
    sqs_client_stub.add_response(
        method="delete_message",
        expected_params={"QueueUrl": "TEST_SQS_URL", "ReceiptHandle": RECEIPT_HANDLE},
        service_response={}
    )

    # We don't explicitly do any assertion as the handler
    # doesn't return anything.
    # Instead the stubbed clients that we are using check if
    # are no pending/additional response made, different from
    # how we defined above. If not, the test will fails.
    handler({}, None)



def test_sqs_queue_contains_placed_order(sqs_client_stub: Stubber, ddb_client_stub: Stubber):
    """
    sqs queue contains order which was PLACED and
    should now be moved to IN_TRANSIT
    """
    # stub receive_message call 
    sqs_client_stub.add_response(
        method="receive_message",
        service_response=SQS_QUEUE_SENDS_MESSAGE,
    )
    # Get Item from DB
    ddb_client_stub.add_response(
        method="get_item",
        expected_params={
            "Key": {"pkey": SQS_ORDER_BODY["pkey"]},
            "TableName": "TEST_TABLE",
        },
        service_response={"Item": utils.serialize_py_to_db(SQS_ORDER_BODY)},
    )
    # Make another call to get Item
    # This is done as part of change_order_status,
    # to fetch the current data in case someone
    # directly updates an order based on its id
    ddb_client_stub.add_response(
        method="get_item",
        expected_params={
            "Key": {"pkey": SQS_ORDER_BODY["pkey"]},
            "TableName": "TEST_TABLE",
        },
        service_response={"Item": utils.serialize_py_to_db(SQS_ORDER_BODY)},
    )
    # PutItem triggered by change_order_status
    ddb_client_stub.add_response(
        method="put_item",
        service_response={},
    )
    # Finally, delete message from SQS
    sqs_client_stub.add_response(
        method="delete_message",
        expected_params={"QueueUrl": "TEST_SQS_URL", "ReceiptHandle": RECEIPT_HANDLE},
        service_response={}
    )
    handler({}, None)