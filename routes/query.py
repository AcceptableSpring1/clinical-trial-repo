from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel
from graph.pipeline import agent
from langfuse.langchain import CallbackHandler
from langchain.messages import HumanMessage, AIMessage
from fastapi_clerk_auth import ClerkConfig, ClerkHTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
import os
import boto3
import uuid
import datetime
import json

load_dotenv()
s3 = boto3.client('s3')

clerk_config = ClerkConfig(jwks_url=os.getenv("CLERK_JWKS_URL"))
clerk_guard = ClerkHTTPBearer(clerk_config)

router = APIRouter()
langfuse_handler = CallbackHandler()

class UserSide(BaseModel):
    trial_id: str
    question: str


@router.options("/query")
async def options_query():
    return Response(status_code=200)

@router.post("/query")
async def user_side(
    item: UserSide,
    creds: HTTPAuthorizationCredentials = Depends(clerk_guard)
    ): 

    user_id = creds.decoded["sub"]
    try: 
       
        conversations = s3.list_objects_v2(Bucket=f"clinical-{user_id}".replace("_", "-").lower(), Prefix=f"{user_id}/{item.trial_id}/")

        previous = [json.loads(s3.get_object(Bucket=f"clinical-{user_id}".replace("_", "-").lower(), Key=convo["Key"])["Body"].read()) for convo in conversations.get("Contents",[])] 

        history = []
        for turn in previous:
           history.append(HumanMessage(content= turn["question"]))
           history.append(AIMessage(content= turn["answer"]))

        messages = await agent.ainvoke(                     
            {"messages":history + [HumanMessage(content=item.question)],
            "trial_id": item.trial_id},
            config = {"callbacks": [langfuse_handler]
            }
        )    
        conversation_turn = {
            "question": item.question,
            "answer": messages["synthesis"],
            "trial_id": item.trial_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        s3.put_object(
            Bucket= f"clinical-{user_id}".replace("_", "-").lower(),
            Key= f"{user_id}/{item.trial_id}/conversation-{uuid.uuid4()}",
            ContentType='application/json',
            Body= json.dumps(conversation_turn)
        )
    except Exception as e:
        print(f"User_side Error: {e} ")
        return{
               "answer": ["Error: issue "] 
            }    
    unique = list(dict.fromkeys(messages["citation"]))  
    return{
            "answer": messages["synthesis"],
            "citations": unique
        }