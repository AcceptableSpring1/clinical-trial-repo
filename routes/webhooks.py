from fastapi import APIRouter, Request, HTTPException, Response, status
from svix.webhooks import Webhook, WebhookVerificationError
import os
import boto3 
import json


s3 = boto3.client('s3')
router = APIRouter()


@router.post("/webhooks/clerk")
async def clerk_webhook(request: Request, response: Response):
    headers = request.headers
    payload = await request.body()
 
    try:
        wh = Webhook(os.getenv("CLERK_WEBHOOK_SECRET"))
        wh.verify(payload, dict(headers))
    except WebhookVerificationError as e:
        print(f"Webhook verification failed: {e}")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return

    data = json.loads(payload)
    
    if data["type"] == "user.created":
        user_id = data["data"]["id"]
        bucket_name = f"clinical-{user_id}".lower()
        bucket_name_final = bucket_name.replace("_", "-")
        s3.create_bucket(Bucket=bucket_name_final)
        return {"status": "success"}
    
    return {"status": "ok"}

@router.get("/health")
async def health_check():
    return {"status": "healthy"}