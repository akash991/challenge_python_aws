from common.errors import ItemNotFound
from common.utils import ORDER_LIFE_CYCLE
from aws_lambda_powertools.logging import Logger
from common.dynamodb import change_order_status, get_item_by_pkey

logger = Logger()

def handler(event, context):
    """
    lambda function to handle update operations
    """
    order_number = event["pkey"]
    try:
        # Check if the order was cancelled or payment did failed
        order_details = get_item_by_pkey(order_number)
        # Order was cancelled
        if order_details["Status"] == ORDER_LIFE_CYCLE.CANCELLED:
            logger.info(f"Order {order_number} was cancelled. Not placing the order")
            return order_details
        # Payment process failed
        elif order_details["Status"] == ORDER_LIFE_CYCLE.FAILED:
            logger.info(f"Payment failed while placing order {order_number}.")
            return order_details
        # Order status remain PROCESSING
        change_order_status(order_number, ORDER_LIFE_CYCLE.PLACED)
        response = get_item_by_pkey(order_number)
        return response
    except ItemNotFound:
        raise

    
