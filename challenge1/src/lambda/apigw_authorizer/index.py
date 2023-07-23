import os


def handler(event, context):
    """
    function to authorize user to trigger api
    endpoint
    """
    methodArn = event["methodArn"]
    auth_param_value = event['authorizationToken']
    if auth_param_value == get_api_id(methodArn):
        return {
            "policyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "execute-api:Invoke",
                        "Effect": "Allow",
                        "Resource": methodArn,
                    }
                ],
            },
            "context": {},
        }


def get_api_id(method_arn):
    """
    method returns API ID from the ARN
    """
    api_details = method_arn.split(":")[-1]
    api_id = api_details.split("/")[0]
    return api_id
