from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
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

        service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "Service",
            cluster=cluster,
            memory_limit_mib=1024,
            desired_count=1,
            cpu=512,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(repo),
                container_port=8000,
                secrets={
                    "OPENAI_API_KEY": ecs.Secret.from_secrets_manager(secret, "OPENAI_API_KEY"),
                    "PINECONE_API_KEY": ecs.Secret.from_secrets_manager(secret, "PINECONE_API_KEY"),
                    "LANGFUSE_SECRET_KEY": ecs.Secret.from_secrets_manager(secret, "LANGFUSE_SECRET_KEY"),
                    "LANGFUSE_PUBLIC_KEY": ecs.Secret.from_secrets_manager(secret, "LANGFUSE_PUBLIC_KEY"),
                    "LANGFUSE_BASE_URL": ecs.Secret.from_secrets_manager(secret, "LANGFUSE_BASE_URL"),
                    "AWS_DEFAULT_REGION": ecs.Secret.from_secrets_manager(secret, "AWS_DEFAULT_REGION"),
                    "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY": ecs.Secret.from_secrets_manager(secret, "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"),
                    "CLERK_SECRET_KEY": ecs.Secret.from_secrets_manager(secret, "CLERK_SECRET_KEY"),
                    "CLERK_JWKS_URL": ecs.Secret.from_secrets_manager(secret, "CLERK_JWKS_URL"),
                    "CLERK_WEBHOOK_SECRET": ecs.Secret.from_secrets_manager(secret, "CLERK_WEBHOOK_SECRET"),
                }
            ),
            listener_port=80,
        )

        service.target_group.configure_health_check(
            path="/health",
            port="8000"
        )

        secret.grant_read(service.task_definition.execution_role)