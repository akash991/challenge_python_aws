import os
import json
import boto3
from common.utils import ORDER_LIFE_CYCLE
from common.dynamodb import change_order_status, get_item_by_pkey
from aws_lambda_powertools.logging import Logger

logger = Logger()
sqs_url = os.environ["ORDERS_SQS_URL"]

sqs_client = boto3.client("sqs")


def handler(event, context):
    """ """
    sqs_message = sqs_client.receive_message(
        QueueUrl=sqs_url,
        MaxNumberOfMessages=1,
        VisibilityTimeout=30,
        WaitTimeSeconds=1
    )

    if not sqs_message.get("Messages") or len(sqs_message["Messages"]) == 0:
        logger.info("No new orders placed")
    else:
        # Get message from the sqs event
        message = sqs_message["Messages"][0]
        # extract receipt handle as its required to delete the message
        receipt_handle = message["ReceiptHandle"]

        # Get the message body
        message_body = json.loads(message["Body"])
        logger.info(f"Message received from sqs is {message_body}")

        # Change Order Status to IN_TRANSIT
        order_number = message_body["pkey"]

        # Check if the Order was cancelled
        current_order_details = get_item_by_pkey(order_number)
        if current_order_details["Status"] == ORDER_LIFE_CYCLE.CANCELLED:
            logger.info(f"Order {order_number} was cancelled, stop further execution.")
        else:
            change_order_status(order_number, ORDER_LIFE_CYCLE.IN_TRANSIT)
            logger.info(f"Order {order_number} is ready for delivery")

        # Delete Message from the Queue
        logger.info("Deleting event from the queue")
        sqs_client.delete_message(QueueUrl=sqs_url, ReceiptHandle=receipt_handle)
        logger.info("Message deleted successfully from SQS")
