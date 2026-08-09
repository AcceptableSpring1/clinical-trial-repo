import boto3
import json
import subprocess

def create_k8s_secret():
    client = boto3.client("secretsmanager", region_name="us-east-1")
    
    response = client.get_secret_value(SecretId="clinical-trial-secrets")
    secrets = json.loads(response["SecretString"])
    
    # Build kubectl command
    cmd = ["kubectl", "create", "secret", "generic", "clinical-trial-secrets"]
    
    for key, value in secrets.items():
        cmd.append(f"--from-literal={key}={value}")
    
    cmd.extend(["--dry-run=client", "-o", "yaml"])
    
    # Generate the secret YAML and apply it
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    apply = subprocess.run(
        ["kubectl", "apply", "-f", "-"],
        input=result.stdout,
        capture_output=True,
        text=True
    )
    
    print(apply.stdout)
    print(apply.stderr)

if __name__ == "__main__":
    create_k8s_secret()