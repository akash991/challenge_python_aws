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
        change_order_status(order_number, ORDER_LIFE_CYCLE.PLACED)
        response = get_item_by_pkey(order_number)
        return response
    except ItemNotFound:
        raise

    
