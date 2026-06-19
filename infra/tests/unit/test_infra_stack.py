import aws_cdk as cdk
from aws_cdk import assertions
from infra.infra_stack import TicketFlowInfraStack

def test_sqs_queue_created():
    app = cdk.App()
    stack = TicketFlowInfraStack(app, "infra")
    template = assertions.Template.from_stack(stack)
