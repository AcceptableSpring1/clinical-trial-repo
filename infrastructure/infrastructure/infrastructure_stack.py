from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
    aws_eks as eks,
    lambda_layer_kubectl_v31 as kubectl_v31
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
        
        cluster = eks.Cluster(self, "ClinicalTrialCluster",
            version=eks.KubernetesVersion.V1_31,
            vpc=vpc,
            default_capacity=1,
            default_capacity_instance=ec2.InstanceType.of(
                ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM
            ),
            kubectl_layer=kubectl_v31.KubectlV31Layer(self, "KubectlLayer")
        )