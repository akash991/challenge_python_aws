import os
import boto3
from common.errors import ItemNotFound
from aws_lambda_powertools.logging import Logger

__table = None
logger = Logger()
orders_table = os.environ["ORDERS_TABLE"]

db_resource = boto3.resource("dynamodb")


def __get_orders_table():
    global __table
    if __table is None:
        __table = db_resource.Table(orders_table)
    return __table


def get_item_by_pkey(value, pkey="pkey"):
    """
    get order details for a given order number
    """
    table = __get_orders_table()
    details = table.get_item(Key={pkey: value})
    try:
        return details["Item"]
    except KeyError:
        raise ItemNotFound()


def change_order_status(order_number, new_status):
    """
    change order status
    """
    table = __get_orders_table()
    order_details = table.get_item(Key={"pkey": order_number})
    try:
        order = order_details["Item"]
    except KeyError:
        raise ItemNotFound()
    if order["Status"] == new_status:
        logger.info(f"Order Status of {order_number} already set to {new_status}")
    else:
        logger.info(f"Updating order Status of {order_number} to {new_status}")
        order["Status"] = new_status
        table.put_item(Item=order)


def order_table_put_item(item_details):
    """
    add new item to the table
    """
    table = __get_orders_table()
    logger.info(f"Adding item: {item_details} to the table")
    table.put_item(Item=item_details)



