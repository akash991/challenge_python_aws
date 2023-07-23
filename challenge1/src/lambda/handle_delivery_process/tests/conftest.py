import os

stub_env_var = {
    "ORDERS_SQS_URL": "TEST_SQS_URL",
    "ORDERS_TABLE": "TEST_TABLE",
}
for k, v in stub_env_var.items():
    os.environ[k] = v

from pytest import fixture
from botocore.stub import Stubber
from common.dynamodb import db_resource
from boto3.dynamodb.types import TypeSerializer
from handle_delivery_process.index import sqs_client


@fixture(autouse=True)
def sqs_client_stub():
    with Stubber(sqs_client) as stubbed:
        yield stubbed
    # assert that there are no pending
    # or extra response that this client
    # didn't handle
    stubbed.assert_no_pending_responses


@fixture(autouse=True)
def ddb_client_stub():
    with Stubber(db_resource.meta.client) as stubbed:
        yield stubbed
    stubbed.assert_no_pending_responses


class utils:
    def serialize_py_to_db(data):
        # Serialize Dynamodb response i.e.
        # change {key:value} -> {key:{type:val}}
        # This is required as we mock dynamodb response
        # in our tests.
        serializer = TypeSerializer()
        return {k: serializer.serialize(v) for k, v in data.items()}
