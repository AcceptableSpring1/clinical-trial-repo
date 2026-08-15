from fastapi import FastAPI
from routes import ingestion, query, webhooks
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.include_router(ingestion.router)
app.include_router(query.router)
app.include_router(webhooks.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
                   "https://clinical-trial-frontend.vercel.app"
                   "https://clinical.zaysprojectsite.com"
                   ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)