from .conftest import utils
from chalice.test import Client
from botocore.stub import Stubber, ANY
from .payload import (
    TABLENAME,
    POST_ORDER_INPUT_JSON,
    POST_ORDER_INPUT_JSON_INVALID,
    DB_PUT_ITEM_EXPECTED_PARAMS,
    DB_GET_ITEM_ORDER_DETAILS,
)

def test_post_order_with_valid_input(
    ddb_client_stub: Stubber,
    stepfunction_client_stub: Stubber,
    stub_api_client: Client,
):
    # mock db put_item call to store new record
    ddb_client_stub.add_response(
        method="put_item",
        expected_params={
            "Item": DB_PUT_ITEM_EXPECTED_PARAMS,
            "TableName": TABLENAME,
        },
        service_response={},
    )
    # mock stepfunction start_execution to trigger the next steps
    stepfunction_client_stub.add_response(
        method="start_execution",
        expected_params={
            "stateMachineArn": "TEST_ARN",
            "name": ANY,
            "input": ANY,
        },
        service_response={
            "executionArn": "test",
            "startDate": "2011-11-11 11:11:11",
        },
    )

    # Creating new Order
    response = stub_api_client.http.post(
        "/order",
        headers=utils.generate_headers(),
        body=utils.json_to_str(POST_ORDER_INPUT_JSON),
    )

    assert response.status_code == 200
    assert response.json_body == {
        "OrderId": "ORD0000001",
        "Message": "Order received, processing payment",
    }


def test_post_order_with_invalid_input(
    stub_api_client: Client,
):
    # no db call as BadRequest Exception is raised
    # no stepfunction call as BadRequest Exception is raised

    # Creating new Order
    response = stub_api_client.http.post(
        "/order",
        headers=utils.generate_headers(),
        body=utils.json_to_str(POST_ORDER_INPUT_JSON_INVALID),
    )
    assert response.status_code == 400
    assert "Invalid json body. Allowed values are:" in response.json_body["Message"]


def test_get_order_with_valid_orderid(
    ddb_client_stub: Stubber,
    stub_api_client: Client,
):
    # mock db put_item call to get record
    ddb_client_stub.add_response(
        method="get_item",
        expected_params={
            "Key": {"pkey": "ORD0000001"},
            "TableName": TABLENAME,
        },
        service_response={
            "Item": utils.serialize_json_to_db(DB_GET_ITEM_ORDER_DETAILS)
        },
    )

    # Get Order details
    response = stub_api_client.http.get(
        "/order/ORD0000001",
        headers=utils.generate_headers(),
    )

    assert response.status_code == 200
    assert response.json_body == DB_GET_ITEM_ORDER_DETAILS


def test_get_order_with_ivalid_orderid_format(
    ddb_client_stub: Stubber,
    stub_api_client: Client,
):
    # mock db put_item call to get record
    ddb_client_stub.add_response(
        method="get_item",
        expected_params={
            "Key": {"pkey": "12345"},
            "TableName": TABLENAME,
        },
        service_response={},
    )

    # Get Order details
    response = stub_api_client.http.get(
        "/order/12345",
        headers=utils.generate_headers(),
    )

    assert response.status_code == 400
    assert (
        response.json_body["Message"]
        == "Order number format is invalid, should be 'ORDXXXXXXX' where X is a number."
    )


def test_get_order_with_orderid_doesnt_exist(
    ddb_client_stub: Stubber,
    stub_api_client: Client,
):
    # mock db put_item call to get record
    ddb_client_stub.add_response(
        method="get_item",
        expected_params={
            "Key": {"pkey": "ORD0000001"},
            "TableName": TABLENAME,
        },
        service_response={},
    )

    # Get Order details
    response = stub_api_client.http.get(
        "/order/ORD0000001",
        headers=utils.generate_headers(),
    )

    assert response.status_code == 400
    assert response.json_body["Message"] == "Order ORD0000001 doesn't exist"


def test_cancel_PLACED_order(
    ddb_client_stub: Stubber,
    stepfunction_client_stub: Stubber,
    stub_api_client: Client,
):
    # mock db put_item call to store new record
    ddb_client_stub.add_response(
        method="put_item",
        expected_params={
            "Item": DB_PUT_ITEM_EXPECTED_PARAMS,
            "TableName": TABLENAME,
        },
        service_response={},
    )
    # mock stepfunction start_execution to trigger the next steps
    stepfunction_client_stub.add_response(
        method="start_execution",
        expected_params={
            "stateMachineArn": "TEST_ARN",
            "name": ANY,
            "input": ANY,
        },
        service_response={
            "executionArn": "test",
            "startDate": "2011-11-11 11:11:11",
        },
    )

    # Creating new Order
    response = stub_api_client.http.post(
        "/order",
        headers=utils.generate_headers(),
        body=utils.json_to_str(POST_ORDER_INPUT_JSON),
    )

    assert response.status_code == 200
    assert response.json_body == {
        "OrderId": "ORD0000001",
        "Message": "Order received, processing payment",
    }

