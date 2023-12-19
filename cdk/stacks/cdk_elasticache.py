# Built-in imports
import os

# External imports
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_ec2,
    aws_lambda,
    aws_elasticache,
    Duration,
)
from constructs import Construct


class ElasticacheStack(Stack):
    """
    Class to create the infrastructure on AWS.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        main_resources_name: str,
        deployment_environment: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Input parameters
        self.construct_id = construct_id
        self.main_resources_name = main_resources_name
        self.deployment_environment = deployment_environment

        # Main methods for the deployment
        self.import_resources()
        self.create_lambda_functions()
        self.create_elasticache_redis()

        # Create CloudFormation outputs
        self.generate_cloudformation_outputs()

    def import_resources(self):
        """
        Import the necessary AWS resources to the stack, for referencing them
        towards other resources/configurations.
        """
        self.vpc = aws_ec2.Vpc.from_lookup(
            self,
            "VPC",
            is_default=True,
        )

    def create_lambda_functions(self):
        """
        Create the Lambda Functions that interact with Redis.
        """

        # Lambda Function's Security Group for more granular control
        self.security_group_lambda = aws_ec2.SecurityGroup(
            self,
            "SG-Lambda",
            description=f"Security Group for {self.main_resources_name} Lambda Functions",
            allow_all_outbound=True,
            vpc=self.vpc,
        )

        # Get relative path for folder that contains Lambda function source
        # ! Note--> we must obtain parent dirs to create path (that"s why there is "os.path.dirname()")
        PATH_TO_LAMBDA_FUNCTION_FOLDER = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "src",
        )
        self.lambda_function: aws_lambda.Function = aws_lambda.Function(
            self,
            id="Lambda",
            allow_public_subnet=True,  # Just for tests, but in prod should be private
            vpc=self.vpc,
            security_groups=[self.security_group_lambda],
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            handler="lambda_function.lambda_handler",
            code=aws_lambda.Code.from_asset(PATH_TO_LAMBDA_FUNCTION_FOLDER),
            timeout=Duration.seconds(15),
            memory_size=128,
            environment={
                "LOG_LEVEL": "DEBUG",
                "ENV": self.deployment_environment,
            },
            log_format=aws_lambda.LogFormat.JSON.value,
            application_log_level=aws_lambda.ApplicationLogLevel.DEBUG.value,
        )

    def create_elasticache_redis(self):
        """
        Create ElastiCache solution for Redis.
        """

        redis_sec_group = aws_ec2.SecurityGroup(
            self,
            "SG-Redis",
            security_group_name="SG-Redis",
            vpc=self.vpc,
            allow_all_outbound=True,
        )
        redis_sec_group.add_ingress_rule(
            peer=self.security_group_lambda,
            description="Allow Redis connection",
            connection=aws_ec2.Port.tcp(6379),
        )

        # Elasticache for Redis Serverless
        self.elasticache = aws_elasticache.CfnServerlessCache(
            self,
            "Redis-Cluster",
            engine="redis",
            serverless_cache_name=f"{self.main_resources_name}-{self.deployment_environment}",
            security_group_ids=[redis_sec_group.security_group_id],
            description="Redis Serverless Cache to be used as primary database",
            subnet_ids=self.vpc.select_subnets(
                subnet_type=aws_ec2.SubnetType.PUBLIC,
                subnet_filters=[
                    aws_ec2.SubnetFilter.availability_zones(
                        availability_zones=[
                            "us-east-1a",
                            "us-east-1b",
                        ]
                    )
                ],
            ).subnet_ids,
        )

        # TODO: Note: as of current CDK version (2.115.0), this returns an error...
        # # Add env-var for Lambda Function to get REDIS endpoint
        # self.lambda_function.add_environment(
        #     "REDIS_HOST", self.elasticache.attr_endpoint.to_string()
        # )

    def generate_cloudformation_outputs(self):
        """
        Method to add the relevant CloudFormation outputs.
        """

        CfnOutput(
            self,
            "DeploymentEnvironment",
            value=self.deployment_environment,
            description="Deployment environment",
        )

        # CfnOutput(
        #     self,
        #     "ElasticacheEndpoint",
        #     value=self.elasticache.attr_endpoint,
        #     description="ElastiCache Endpoint for Redis",
        # )
