import httpx
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone
from dotenv import load_dotenv
from openai import OpenAI
from typing import Annotated
import pdfplumber
import io
load_dotenv()
client = OpenAI()
pc = Pinecone()
index = pc.Index(host="https://clinical-trial-test-two-4pv7yax.svc.aped-4627-b74a.pinecone.io")

# Change NCT number to ingest a different trial
response = httpx.get("https://clinicaltrials.gov/api/v2/studies/NCT03924869")
data = response.json()
# print(json.dumps(data, indent=2))
print(data["protocolSection"]["identificationModule"])

hasPDF = data["documentSection"]["largeDocumentModule"]["largeDocs"][0]["hasProtocol"]
nameFile = data["documentSection"]["largeDocumentModule"]["largeDocs"][0]["filename"]
nct_id = data["protocolSection"]["identificationModule"]["nctId"]
title = data["protocolSection"]["identificationModule"]["briefTitle"]
nct_suffix = nct_id[-2:]
dynURL = f'https://clinicaltrials.gov/ProvidedDocs/{nct_suffix}/{nct_id}/{nameFile}'
namespace = title.replace(" ", "_").lower()

def ingest_doc(pdf_bytes: bytes, trial_id: str):
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:

        text = ""

        for page in pdf.pages:
            text += page.extract_text()

        splitter = RecursiveCharacterTextSplitter(
                chunk_size=1500,
                chunk_overlap=150
            )
        chunks = splitter.split_text(text)

        embeddings = []
        vectors = []

        for i, chunk in enumerate(chunks):
            embeddings.append(client.embeddings.create(input=chunk, model="text-embedding-3-small").data[0].embedding)
            
            classification = client.chat.completions.create(
                    model="gpt-5-nano", 
                    messages=[{
                    "role":"system", "content": "You are to receive these chunks of sentences from a clinical trial document. Return only one category label from this list that best describes the chunk as a whole. Return nothing else — just the category name.You are to best classify those list of sentences as best you can with the following categories. Study Overview, Contacts and location, Participation Criteria, Medication, Outcome meeasures, Study Record Dates, Adverse events, Limitaions caveats, outcome measure"}, 
                    {"role":"user", "content":chunk}
                    ]
                    )
        
            section = classification.choices[0].message.content.strip() 
    # Build vectors for Pinecone
            vectors.append({"id": f"rec{i}", "values": embeddings[-1], "metadata": {"text": chunk, "section": section}})


# Upsert to Pinecone
    index.upsert(vectors=vectors, namespace=trial_id)

    return {"file_size": len(chunks)}

if hasPDF == True:
    with httpx.stream("GET", dynURL, follow_redirects=True) as r:
        pdf_bytes = b"".join(r.iter_bytes())   
    ingest_doc(pdf_bytes, namespace)
else:     
    print("No PDF Found")
