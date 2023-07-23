import re
import os
import json
import boto3
from schema import SchemaError
from aws_lambda_powertools.logging import Logger
from chalicelib.schemas import post_order_schema
from chalicelib.utils import generate_order_number
from chalice import Chalice, BadRequestError, CustomAuthorizer

try:
    from common.errors import ItemNotFound
    from common.utils import ORDER_LIFE_CYCLE
    from common.dynamodb import get_item_by_pkey, order_table_put_item
except ModuleNotFoundError:
    pass


logger = Logger()
app = Chalice(app_name="restapi")
sf_client = boto3.client("stepfunctions")

LAMBDA_FUNCTION_AUTHORIZER_URI = os.environ["LAMBDA_FUNCTION_AUTHORIZER_URI"]
PAYMENT_PROCESSING_SF_ARN = os.environ["PAYMENT_PROCESSOR_SF_ARN"]
APIGW_INVOKE_LAMBDA_ROLE_ARN = os.environ["APIGW_INVOKE_LAMBDA_ROLE_ARN"]


# custom authorizer for orders API
authorizer = CustomAuthorizer(
    name="api-gw-custom-auth",
    authorizer_uri=LAMBDA_FUNCTION_AUTHORIZER_URI,
    invoke_role_arn=APIGW_INVOKE_LAMBDA_ROLE_ARN,
    header="authorizationToken",
    ttl_seconds=0
)


@app.route("/", authorizer=authorizer)
def index():
    return {"hello": "world"}


@app.route("/order", methods=["POST"], authorizer=authorizer)
def create_new_order():
    """
    method to create new order details
    """
    current_request_body = app.current_request.json_body
    try:
        post_order_schema.validate(current_request_body)
    except SchemaError:
        return BadRequestError(
            f"Invalid json body. Allowed values are: {post_order_schema.schema}"
        )

    # Generate a new order number
    order_number = generate_order_number()
    # Set pkey, skey and Order Status
    current_request_body["pkey"] = order_number
    current_request_body["OrderedBy"] = "dummy@dummy.com"
    current_request_body["Status"] = ORDER_LIFE_CYCLE.PROCESSING

    order_table_put_item(current_request_body)
    logger.info(
        f"Order: {current_request_body} added to the table, triggering step function to process payment"
    )

    sf_client.start_execution(
        stateMachineArn=PAYMENT_PROCESSING_SF_ARN,
        name=f"process_payment_{order_number}",
        input=json.dumps(current_request_body),
    )

    return {"Message": f"Order received, processing payment for OrderId {order_number}"}


@app.route("/order/{order_number}", methods=["GET"], authorizer=authorizer)
def get_order_details(order_number):
    """
    method to get order details
    """
    if not re.match("^ORD\d{7}$", order_number):
        return BadRequestError(
            "order_number format is invalid, should be 'ORDXXXXXXX' where X is a number."
        )

    try:
        response = get_item_by_pkey(order_number)
    except ItemNotFound:
        logger.error(
            f"Invalid Order number {order_number}, please try with a valid order number"
        )

    logger.info(f"Records found for order number {order_number}")
    return response


@app.route("/cancel/{order_number}", methods=["PUT"], authorizer=authorizer)
def cancel_order(order_number):
    """
    method to cancel existing order
    """
    if not re.match("^ORD\d{7}$", order_number):
        return BadRequestError(
            "order_number format is invalid, should be 'ORDXXXXXXX' where X is a number."
        )

    try:
        response = get_item_by_pkey(order_number)
    except ItemNotFound:
        logger.error(
            f"Invalid Order number {order_number}, please try with a valid order number"
        )

    logger.info(f"Records found for order number {order_number}, checking its Status")

    # ORDER IS DELIVERED
    if response["Status"] == ORDER_LIFE_CYCLE.COMPLETED:
        api_response = {
            "Message": "Product already delivered, you can opt for an exchange"
        }
    # ORDER IS PLACED OR IN_TRANSIT
    elif response["Status"] in [ORDER_LIFE_CYCLE.IN_TRANSIT, ORDER_LIFE_CYCLE.PLACED]:
        api_response = {"Message": "Order is cancelled, your refund is initiated"}
        response["Status"] = ORDER_LIFE_CYCLE.CANCELLED
    else:
        api_response = {
            "Message": "Order already cancelled or was never placed successfully"
        }
        response["Status"] = ORDER_LIFE_CYCLE.CANCELLED

    order_table_put_item(response)
    return api_response
