from schema import Schema, Forbidden, Optional

__post_order_schema_dict = {
    Forbidden("pkey"): str,
    Forbidden("OrderedBy"): str,
    "Item": str,
    "Amount": int,
    Optional("Description"): str
}

post_order_schema = Schema(__post_order_schema_dict)
