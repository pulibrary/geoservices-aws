import aws_cdk as core
import aws_cdk.assertions as assertions

from geoservices.geoservices_stack import GeoservicesStack

# example tests. To run these tests, uncomment this file along with the example
# resource in geoservices/geoservices_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = GeoservicesStack(app, "geoservices")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
