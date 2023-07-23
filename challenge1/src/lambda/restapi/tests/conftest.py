import os

# Stub environment variables
for key in [
    "PAYMENT_PROCESSOR_SF_ARN",
    "LAMBDA_FUNCTION_AUTHORIZER_URI",
    "APIGW_INVOKE_LAMBDA_ROLE_ARN",
]:
    os.environ[key] = ""
