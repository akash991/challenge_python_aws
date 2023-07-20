# Assumptions made:
# =================
# 1. object: type dictionary
# 2. object.key: type string
# 3. object.value: type string/dictionary
# 4. Argument 'key' should never be empty
# 5. Function should handle all possible exceptions 
#    instead of throwing exception and returns None
# 6. Argument 'key' is a valid path if it points to a string. 
#    For eg. a/b is not valid in {a:{b:{c:d}}} as its value is {c:d}.
#    I've used an optional input parameter 'only_str' to toggle this behavior,
#    with default value as True, it will return None in the above example.
#    When explicitly passed as False, it will return whatever the value is.

DELIMITER = "/"

def parse(object: dict, key: str, only_str=True):
    """
    parse object and return value for the given key
    """
    _object = object

    # return if key is empty
    if key == "":
        print("Empty key is not allowed")
        return
    
    # split key at the delimiter
    key_items = key.split(DELIMITER)

    while len(key_items) > 0:
        curr_item = key_items.pop(0)

        try:
            _object = _object[curr_item]
        except (KeyError, ValueError):
            print(f"Path {key} doesn't exist")
            return

    if only_str:
        if not isinstance(_object, str):
            print(f"Key {key} is not a string, please check the path")
            return

    return _object
