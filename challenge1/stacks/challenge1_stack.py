import os
from aws_cdk import (
    Stack,
    Duration,
    aws_lambda,
    aws_iam as iam,
    aws_sqs as sqs,
    BundlingOptions,
    aws_events as events,
    aws_cognito as cognito,
    aws_stepfunctions as sf,
    aws_dynamodb as dynamodb,
    aws_events_targets as event_target,
    aws_stepfunctions_tasks as sf_tasks,
)
from chalice.cdk import Chalice
from constructs import Construct


class Challenge1Stack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # dynamodb table to store order details
        self.orders_table = dynamodb.Table(
            self,
            id="OrdersTable",
            table_name="users-orders-table",
            deletion_protection=True,
            time_to_live_attribute="TTL",
            partition_key=dynamodb.Attribute(
                name="pkey",
                type=dynamodb.AttributeType.STRING,
            ),
        )

        # Add orderedby as secondary index to fetch orders
        # based on who ordered it.
        self.orders_table.add_global_secondary_index(
            partition_key=dynamodb.Attribute(
                name="OrderedBy", type=dynamodb.AttributeType.STRING
            ),
            index_name="OrderedBy-index",
            projection_type=dynamodb.ProjectionType.ALL
        )

        # DLQ to receive orders with processing errors
        self.sqs_new_orders_dlq = sqs.Queue(
            self,
            id="NewOrdersDLQ",
            queue_name="orders-dl-queue",
            visibility_timeout=Duration.minutes(2),
        )

        # SQS Queue to receive order details after successful payment
        self.sqs_new_orders = sqs.Queue(
            self,
            id="NewOrdersSQS",
            queue_name="orders-queue",
            visibility_timeout=Duration.minutes(2),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=1, queue=self.sqs_new_orders_dlq
            ),
        )

        # Update SQS resource based policy to let
        self.sqs_new_orders.add_to_resource_policy(
            statement=iam.PolicyStatement(
                actions=["sqs:*"],
                effect=iam.Effect.ALLOW,
                resources=[self.sqs_new_orders.queue_arn],
                principals=[
                    iam.ArnPrincipal(self.account).with_conditions(
                        {
                            "StringLike": {
                                "aws:PrincipalArn": [
                                    f"arn:aws:lambda::{self.account}:function:*"
                                ]
                            }
                        }
                    )
                ],
            )
        )

        # Lambda layer creation
        self.common_lambda_layer = aws_lambda.LayerVersion(
            self,
            id="CommonLambdaLayer",
            layer_version_name="common-lambda-layer",
            compatible_architectures=[aws_lambda.Architecture.X86_64],
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_9],
            code=aws_lambda.Code.from_asset(
                path=os.path.join(os.path.dirname(__file__), "..", "src", "layers"),
                bundling=BundlingOptions(
                    image=aws_lambda.Runtime.PYTHON_3_9.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output/python && cp -r common /asset-output/python",
                    ],
                ),
            ),
        )

        # Lambda role to query sqs and move order status to IN_TRANSIT
        self.lambda_handle_delivery_role = iam.Role(
            self,
            id="LambdaHandleInTransitRole",
            role_name="order-delivery-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "logging": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW, actions=["logs:*"], resources=["*"]
                        )
                    ]
                ),
                "sqs": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "sqs:DeleteMessage",
                                "sqs:ReceiveMessage",
                            ],
                            resources=[self.sqs_new_orders.queue_arn],
                        )
                    ]
                ),
                "dynamodb": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:GetItem",
                                "dynamodb:PutItem",
                            ],
                            resources=[self.orders_table.table_arn],
                        )
                    ]
                ),
            },
        )

        # lambda function to handle delivery process
        self.handle_delivery_lambda = aws_lambda.Function(
            self,
            id="HandleDeliveryLambda",
            function_name="handle-delivery",
            role=self.lambda_handle_delivery_role,
            timeout=Duration.seconds(30),
            layers=[self.common_lambda_layer],
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            description="Lambda to trigger the delivery process",
            code=aws_lambda.Code.from_asset(
                path=os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "src",
                    "lambda",
                    "handle_delivery_process",
                )
            ),
            environment={
                "ORDERS_TABLE": self.orders_table.table_name,
                "ORDERS_SQS_URL": self.sqs_new_orders.queue_url,
            },
            handler="index.handler",
        )

        # Eventbridge Rule to trigger delivery handler every min
        self.delivery_handler_eb_trigger = events.Rule(
            self,
            id="DeliveryHandlerCronJob",
            rule_name="order-delivery-handler-cron",
            schedule=events.Schedule.rate(Duration.minutes(1)),
            targets=[event_target.LambdaFunction(handler=self.handle_delivery_lambda)],
        )

        # IAM role for rest api
        self.api_handler_role = iam.Role(
            self,
            id="RestAPIRole",
            role_name="order-handler-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )

        # Allow logging
        self.api_handler_role.add_to_policy(
            statement=iam.PolicyStatement(
                actions=["logs:*"], effect=iam.Effect.ALLOW, resources=["*"]
            )
        )

        # Allow trigerring stepfunction
        self.api_handler_role.add_to_policy(
            statement=iam.PolicyStatement(
                actions=["states:StartExecution"],
                effect=iam.Effect.ALLOW,
                resources=["*"],
            )
        )

        # Allow DB Access
        self.api_handler_role.add_to_policy(
            statement=iam.PolicyStatement(
                actions=["dynamodb:*"],
                effect=iam.Effect.ALLOW,
                resources=[self.orders_table.table_arn],
            )
        )

        # IAM role for lambda to update order details
        self.iam_role_lambda_update_role = iam.Role(
            self,
            id="UpdateOrderTable",
            role_name="update-orders",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "policies": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW, actions=["logs:*"], resources=["*"]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:GetItem",
                                "dynamodb:PutItem",
                            ],
                            resources=[self.orders_table.table_arn],
                        ),
                    ]
                )
            },
        )

        # Lambda function to update order details
        self.lambda_update_order_status = aws_lambda.Function(
            self,
            id="UpdateOrderDetailsLambda",
            function_name="update-order-lambda",
            role=self.iam_role_lambda_update_role,
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            timeout=Duration.seconds(30),
            layers=[self.common_lambda_layer],
            code=aws_lambda.Code.from_asset(
                path=os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "src",
                    "lambda",
                    "orders_table_update_status",
                )
            ),
            handler="index.handler",
            environment={
                # fix me
                "ORDERS_TABLE": self.orders_table.table_name
            },
        )

        sf_update_status_to_ordered_task = sf_tasks.LambdaInvoke(
            self,
            id="Update Order Status",
            lambda_function=self.lambda_update_order_status,
        )

        sf_send_event_to_sqs = sf_tasks.SqsSendMessage(
            self,
            id="Send Message to Order Queue",
            queue=self.sqs_new_orders,
            comment="Send event to Order Queue to start the delivery process",
            message_body=sf.TaskInput.from_json_path_at("$.Payload"),
        )

        sf_wait_30s_task = sf.Wait(
            self,
            id="Mock Payment Process (Wait 1 min)",
            time=sf.WaitTime.duration(Duration.seconds(30)),
            comment="Mocking payment process",
        )

        sf_payment_failed_timedout = sf.Fail(
            self,
            id="Payment Failed or Timed Out",
        )

        sf_definition_body_process_order_payment = sf.DefinitionBody.from_chainable(
            sf_wait_30s_task.next(sf_update_status_to_ordered_task).next(
                sf.Choice(
                    self,
                    id="Order Completed?",
                )
                .when(
                    sf.Condition.string_equals("$.Payload.Status", "PLACED"),
                    sf_send_event_to_sqs,
                )
                .otherwise(sf_payment_failed_timedout)
            )
        )

        # Stepfunction that is triggered when a new order
        # is placed.
        # Note: This is a very basic function, the idea is to
        # show how different tasks can be orchestrated based
        # on actual requirements.
        self.stepfunction_process_order_payments = sf.StateMachine(
            self,
            id="ProcessNewOrders",
            definition_body=sf_definition_body_process_order_payment,
            state_machine_name="process-new-order-payment",
            timeout=Duration.seconds(70),
        )

        self.chalice_iam_role = iam.Role(
            self,
            id="OrderRestApiRole",
            role_name="order-restapi-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "logging": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW, actions=["logs:*"], resources=["*"]
                        )
                    ]
                ),
                "dynamodb": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["dynamodb:*"],
                            resources=[self.orders_table.table_arn],
                        )
                    ]
                ),
                "stepfunctions": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["states:StartExecution"],
                            resources=[
                                self.stepfunction_process_order_payments.state_machine_arn
                            ],
                        )
                    ]
                ),
            },
        )

        chalice_environment = {
            "ORDERS_TABLE": self.orders_table.table_name,
            "ORDERS_SQS_URL": self.sqs_new_orders.queue_url,
            "PAYMENT_PROCESSOR_SF_ARN": self.stepfunction_process_order_payments.state_machine_arn,
        }

        chalice_stage_config = {
            "automatic_layer": False,
            "manage_iam_role": False,
            "lambda_memory_size": 128,
            "lambda_timeout": 30,
            "environment_variables": chalice_environment,
            "layers": [self.common_lambda_layer.layer_version_arn],
            "iam_role_arn": self.chalice_iam_role.role_arn,
        }

        self.chalice_app = Chalice(
            self,
            id="OrdersRestApi",
            source_dir=os.path.join(
                os.path.dirname(__file__),
                "..",
                "src",
                "lambda",
                "restapi",
            ),
            stage_config=chalice_stage_config,
        )
