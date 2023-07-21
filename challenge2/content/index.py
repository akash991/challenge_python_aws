import sys
import time
import json
import requests

METADATA_BASE_URL = "http://169.254.169.254/latest/meta-data/"
API_TOKEN_URL = "http://169.254.169.254/latest/api/token"
API_TOKEN_HEADER = "X-aws-ec2-metadata-token"
API_TOKEN_TTL_HEADER = "X-aws-ec2-metadata-token-ttl-seconds"
TOKEN_TTL_SECONDS = 3600

__token, __token_gen_epoch = None, 0

# Custom Exception to handle 404 error
class InvalidPath(Exception):
    pass


def __print_helpstring():
    """
    function to print the user helpstring
    """
    print(
        """
This script prints the instance metadata.
You can either get complete metadata or provide a path as argument to fetch a specific key.

For example:
    To fetch the full metadata run: `python ./index.py`
    To fetch the value of http://169.254.169.254/latest/meta-data/<path>, run: `python ./index.py <path>`
"""
    )


def __set_access_token():
    """
    set access_token and generation time
    """
    global __token, __token_gen_epoch
    response = requests.put(
        url=API_TOKEN_URL,
        headers={
            API_TOKEN_TTL_HEADER: str(TOKEN_TTL_SECONDS),
        },
    )
    __token = response.text
    __token_gen_epoch = time.time()


def __refresh_token():
    """
    set token if not already set or expired
    """
    if __token is None:
        __set_access_token()

    elif time.time() - __token_gen_epoch > TOKEN_TTL_SECONDS:
        __set_access_token()

    return __token


def __get_data(url):
    """
    get instance metadata response for a given url
    """
    response = requests.get(
        url=url,
        headers={API_TOKEN_HEADER: get_access_token()},
    )
    if response.status_code == 404:
        raise InvalidPath()
    return response.text


def get_access_token():
    """
    get API access token
    """
    return __refresh_token()


def __get_metadata(url, data={}):
    """
    get instance metadata
    """
    __response = __get_data(url)
    if not url.endswith("/"):
        try:
            return json.loads(__response)
        except json.JSONDecodeError:
            return __response
    else:
        __response = __response.split("\n")
        for key in __response:
            if key.endswith("/"):
                key = key.rstrip("/")
                data[key] = {}
                __get_metadata(f"{url}{key}/", data[key])
            else:
                data[key] = __get_metadata(f"{url}{key}", data)
    return json.dumps(data)


def get_metadata(path=None):
    if not path or path == METADATA_BASE_URL:
        key = METADATA_BASE_URL
    else:
        key = f"{METADATA_BASE_URL}{path}"
    try:
        return __get_metadata(key)
    except InvalidPath:
        print(f"Key: {key} is not valid.")


if __name__ == "__main__":
    args = sys.argv
    if len(args) == 1:
        print(get_metadata())
    elif len(args) == 2 and args[1].lower() in ["-h", "--help"]:
        __print_helpstring()
    elif len(args) == 2:
        print(get_metadata(args[1]))
    else:
        raise Exception("Invalid arguments passed, pass --help as argument")
