import os
import boto3
from common.utils import ORDER_LIFE_CYCLE
from common.dynamodb import change_order_status
from aws_lambda_powertools.logging import Logger

logger = Logger()
sqs_url = os.environ["ORDERS_SQS_URL"]

sqs_resource = boto3.resource("sqs")
queue = sqs_resource.Queue(url=sqs_url)


def handler(event, context):
    """
    """
    sqs_message = queue.receive_messages(
        MaxNumberOfMessages=1,
        VisibilityTimeout=30,
    )
    logger.info(f"Message received from sqs is {sqs_message}")

    if len(sqs_message) == 0:
        logger.info("No new orders placed")
    else:
        message = sqs_message[0]
        logger.info(f"Message received from sqs is {message}")
        order_number = message["pkey"]
        status = ORDER_LIFE_CYCLE.IN_TRANSIT
        change_order_status(order_number, status)
        logger.info(f"Order status updated for order number {order_number}")
        logger.info("Deleting event from Orders queue")
        # queue.delete_messages()
