from fastapi import FastAPI
from routes import ingestion, query, webhooks
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "https://clinical-trial-frontend.vercel.app", 
        "https://clinical.zaysprojectsite.com" 
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )

app.include_router(ingestion.router)
app.include_router(query.router)
app.include_router(webhooks.router)