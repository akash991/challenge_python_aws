from common.errors import ItemNotFound
from common.dynamodb import get_item_by_pkey, order_table_put_item


def generate_order_number():
    try:
        order_number_data = get_item_by_pkey("next_order")
        order_number = order_number_data["number"] + 1
    except ItemNotFound:
        # First order so no record found
        order_number = 1
    order_table_put_item(
        {
            "pkey": "next_order",
            "number": order_number,
        }
    )
    return "ORD" + "0" * (7 - len(str(order_number))) + str(order_number)
