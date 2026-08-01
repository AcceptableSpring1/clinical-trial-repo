from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone
from dotenv import load_dotenv
from fastapi import APIRouter, File, UploadFile
from openai import OpenAI
from typing import Annotated
import fitz

load_dotenv()
router = APIRouter()
client = OpenAI()
pc = Pinecone()
index = pc.Index(host="https://clinical-trial-test-two-4pv7yax.svc.aped-4627-b74a.pinecone.io")

@router.post("/ingestion")
async def ingest_doc(file:UploadFile, trial_id: str):
    contents = await file.read()
    doc = fitz.open(stream=contents, filetype="pdf")

    text = ""

    for page in doc:
        text += page.get_text()

    splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
    chunks = splitter.split_text(text)

    embeddings = [
        client.embeddings.create(input=chunk, model="text-embedding-3-small").data[0].embedding
        for chunk in chunks
    ]

# Build vectors for Pinecone
    vectors = [
        {"id": f"rec{i}", "values": embeddings[i], "metadata": {"text": chunks[i]}}
        for i in range(len(chunks))
]

# Upsert to Pinecone
    index.upsert(vectors=vectors, namespace=trial_id)

    return {"file_size": len(chunks)}


