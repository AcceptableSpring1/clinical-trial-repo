from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam
    # Duration,
    # aws_sqs as sqs,
)
from constructs import Construct

class InfrastructureStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        secret = secretsmanager.Secret.from_secret_complete_arn(
            self, "ClinicalTrialSecrets",
            "arn:aws:secretsmanager:us-east-1:538565434143:secret:clinical-trial-secrets-r6F0yM"
        )
        repo = ecr.Repository.from_repository_name(self, "ClinicalTrialRepo", "clinical-trial-assistant")
        vpc = ec2.Vpc(self, "ClinicalTrialVpc", max_azs=2)
        cluster = ecs.Cluster(self, "ClinicalTrialCluster", vpc=vpc)

    #     s3.Bucket(self, "Bucket",
    #         auto_delete_objects = True,
    #         block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
    #         bucket_name= "clinica-trial-538565434143",
    #         versioned=True,
    #         removal_policy=RemovalPolicy.DESTROY
    # )
        
      
        service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "Service",
            cluster=cluster,
            memory_limit_mib=1024,
            desired_count=1,
            cpu=512,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(repo, 
                tag=None),
                container_port=8000,
                secrets = {
                    "OPENAI_API_KEY": ecs.Secret.from_secrets_manager(secret, "OPENAI_API_KEY"),
                    "PINECONE_API_KEY": ecs.Secret.from_secrets_manager(secret, "PINECONE_API_KEY"),
                    "LANGFUSE_SECRET_KEY": ecs.Secret.from_secrets_manager(secret, "LANGFUSE_SECRET_KEY"),
                    "LANGFUSE_PUBLIC_KEY": ecs.Secret.from_secrets_manager(secret, "LANGFUSE_PUBLIC_KEY"),
                    "LANGFUSE_BASE_URL": ecs.Secret.from_secrets_manager(secret, "LANGFUSE_BASE_URL"),
                    "AWS_REGION_NAME": ecs.Secret.from_secrets_manager(secret, "AWS_REGION_NAME"),
                    "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY": ecs.Secret.from_secrets_manager(secret, "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"),
                    "CLERK_SECRET_KEY": ecs.Secret.from_secrets_manager(secret, "CLERK_SECRET_KEY"),
                    "CLERK_JWKS_URL": ecs.Secret.from_secrets_manager(secret, "CLERK_JWKS_URL"),
                    "CLERK_WEBHOOK_SECRET": ecs.Secret.from_secrets_manager(secret, "CLERK_WEBHOOK_SECRET"),
                }
            ),
            min_healthy_percent=100,
            listener_port=80,

    )
        secret.grant_read(service.task_definition.execution_role)
        service.target_group.configure_health_check(
            path="/health",
            port="8000"
        )

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "InfrastructureQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )
