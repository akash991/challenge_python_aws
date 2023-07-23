# A simple python script to trigger the different apigw endpoints

# What you should do before execution?
# ------------------------------------
# Update 'url' with the api gateway url 

# What this script does:
# ----------------------
# 1) Places an order
# 2) Waits 5 sec then gets the order status
# 3) Cancels the order
# 4) Waits 5 sec then gets the order status

# What you can do?
# ----------------
# Run the script as it is and verify the order status in db and payment
# processor step function (It should fail as we cancelled the order)
# stepfunction name: process-new-order-payment
# dynamodb table: users-orders-table
#                           OR
# Play around with the sleep time and see how the behavior changes

import os
import json
import requests
from time import sleep


url = "Provide your url here"


def getAuthToken():
    # Pass authentication token
    # along with the request.
    # For demonstartion purpose, I'm 
    # using the api-gw id which can be
    # extracted from the endpoint url.
    endpoint_items = url.split(".")
    __gw_id = endpoint_items[0].split("/")[-1]
    return __gw_id


def create_new_order(item, amount, description=None):
    # creating the json body
    json_body = {"Item": item, "Amount": amount}
    if description:
        json_body["Description"] = description
    # sending requests
    __response = requests.post(
        url=os.path.join(url, "order"),
        headers={
            "authorizationToken": getAuthToken(),
        },
        json=json_body,
    )
    if __response.status_code == 200:
        print(__response.text)
        response = json.loads(__response.text)
        return response["OrderId"]
    else:
        print(f"Execution failed, response message: {__response.text}")


def get_order_status(order_id):
    __response = requests.get(
        url=os.path.join(url, "order", order_id),
        headers={
            "authorizationToken": getAuthToken(),
        },
    )
    if __response.status_code == 200:
        print(__response.text)
        return __response.text
    else:
        print(f"Execution failed, response message: {__response.text}")


def cancel_order(order_id):
    __response = requests.put(
        url=os.path.join(url, "cancel", order_id),
        headers={
            "authorizationToken": getAuthToken(),
        },
    )
    if __response.status_code == 200:
        print(__response.text)
        return __response.text
    else:
        print(f"Execution failed, response message: {__response.text}")


item: str = "test_item"
ammount: int = 100
description: str = "Description for item_test"

# Create new Order
print("Creating new order")
order_id = create_new_order(
    item=item,
    amount=ammount,
    description=description,
)
sleep(5)
# Get Order Status
print("Getting order status")
get_order_status(order_id=order_id)
# Cancel Order
print("Cancelling order")
cancel_order(order_id=order_id)
sleep(5)
# Get Order Status after Cancellation
print("Getting order status")
get_order_status(order_id=order_id)
