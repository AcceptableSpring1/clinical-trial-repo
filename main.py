from fastapi import FastAPI
from routes import ingestion, query, webhooks

app = FastAPI()
app.include_router(ingestion.router)
app.include_router(query.router)
app.include_router(webhooks.router)