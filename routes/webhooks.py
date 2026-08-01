from fastapi import APIRouter, Request, HTTPException, Response, status
from svix.webhooks import Webhook, WebhookVerificationError
import os
import boto3 


s3 = boto3.client('s3')
router = APIRouter()


@router.post("/webhooks/clerk")
async def clerk_webhook(request: Request, response: Response):

    headers = request.headers
    payload = await request.body()
 
    try:
        wh = Webhook(os.getenv("CLERK_WEBHOOK_SECRET"))
        msg = wh.verify(payload, headers)

        if msg["type"] == "user.created":
            user_id = msg["data"]["id"]
            bucket_name = f"clinical-{user_id}".lower()
            bucket_name_final = bucket_name.replace("_", "-")
            response = s3.create_bucket(Bucket= bucket_name_final)

            return {"status": "success"}

    except WebhookVerificationError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return
@router.get("/health")
async def health_check():
    return {"status": "healthy"}