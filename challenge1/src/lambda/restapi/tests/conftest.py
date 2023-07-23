import os
import json

# Stub environment variables
stub_env_variables = {
    "PAYMENT_PROCESSOR_SF_ARN": "TEST_ARN",
    "LAMBDA_FUNCTION_AUTHORIZER_URI": "TEST_URI",
    "APIGW_INVOKE_LAMBDA_ROLE_ARN": "TEST_ARN",
    "ORDERS_TABLE": "TEST_TABLE",
}
for key, val in stub_env_variables.items():
    os.environ[key] = val

from restapi import app
from pytest import fixture
from chalice.test import Client
from unittest.mock import patch
from botocore.stub import Stubber
from common.dynamodb import db_resource
from boto3.dynamodb.types import TypeSerializer


@fixture(autouse=True)
def ddb_client_stub():
    with Stubber(db_resource.meta.client) as stubbed_db:
        yield stubbed_db
    stubbed_db.assert_no_pending_responses


@fixture(autouse=True)
def stub_generate_order_number():
    with patch("restapi.app.generate_order_number") as patched:
        patched.return_value = "ORD0000001"
        yield patched


@fixture(autouse=True)
def stepfunction_client_stub():
    with Stubber(app.sf_client) as stubbed_sf:
        yield stubbed_sf
    stubbed_sf.assert_no_pending_responses


@fixture
def stub_api_client():
    with Client(app.app) as stubbed_client:
        yield stubbed_client


class utils:
    def generate_headers():
        return {"Content-Type": "application/json"}

    def json_to_str(json_body):
        return json.dumps(json_body)

    def serialize_json_to_db(json_body):
        serializer = TypeSerializer()
        return {k: serializer.serialize(v) for k, v in json_body.items()}
