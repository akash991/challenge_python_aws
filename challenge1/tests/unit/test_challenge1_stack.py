import aws_cdk as core
import aws_cdk.assertions as assertions

from challenge1.challenge1_stack import Challenge1Stack

# example tests. To run these tests, uncomment this file along with the example
# resource in challenge1/challenge1_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = Challenge1Stack(app, "challenge1")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
