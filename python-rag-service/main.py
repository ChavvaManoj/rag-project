from fastapi import FastAPI, UploadFile, File
import shutil
import os
import re

from pypdf import PdfReader
from pydantic import BaseModel

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma

from dotenv import load_dotenv
load_dotenv()
# -------------------------------
# 🚀 Initialize FastAPI
# -------------------------------
app = FastAPI()

# -------------------------------
# 📂 Setup folders
# -------------------------------
UPLOAD_DIR = "uploaded_docs"
CHROMA_DIR = "chroma_db"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# -------------------------------
# 🧠 Initialize Embeddings + DB
# -------------------------------
embedding = OpenAIEmbeddings()

vector_store = Chroma(
    collection_name="documents",
    embedding_function=embedding,
    persist_directory=CHROMA_DIR
)
# -------------------------------
# 🤖 Initialize LLM
# -------------------------------
llm = ChatOpenAI(
    model="gpt-3.5-turbo",   # or "gpt-4o-mini"
    temperature=0
)

# -------------------------------
# 📄 PDF Text Extraction
# -------------------------------
def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""

    return text

# -------------------------------
# ✂️ Chunking Logic
# -------------------------------
def chunk_text(text, chunk_size=500, overlap=100):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)

    return chunks

# -------------------------------
# 🧪 Health Check
# -------------------------------
@app.get("/")
def health():
    return {"status": "Python RAG service running"}

# -------------------------------
# 📥 Ingest API
# -------------------------------
@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):

    print("🔥 File received:", file.filename)

    filename = file.filename

    # Validate filename
    if not filename:
        return {"error": "Invalid file name"}

    # Clean filename
    safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)

    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print("✅ File saved at:", file_path)

    # Extract text
    text = extract_text_from_pdf(file_path)

    if not text.strip():
        return {"message": "No text found in PDF"}

    # Chunk text
    chunks = chunk_text(text)

    print(f"📦 Total chunks created: {len(chunks)}")

    # Store embeddings
    vector_store.add_texts(chunks)

    print("🧬 Stored embeddings in ChromaDB")

    return {
        "message": "File processed and stored",
        "chunks": len(chunks)
    }

# -------------------------------
# 🔍 Query API
# -------------------------------
class QueryRequest(BaseModel):
    query: str



@app.post("/query")
async def query_rag(request: QueryRequest):

    query = request.query

    print("🔍 Query received:", query)

    docs = vector_store.similarity_search(query, k=3)

    context = "\n\n".join([doc.page_content for doc in docs])

    prompt = f"""
You are a helpful AI assistant.

Answer the question ONLY using the context below.
If the answer is not present, say "I don't know".

Context:
{context}

Question:
{query}
"""

    response = llm.invoke(prompt)

    return {
        "query": query,
        "answer": response.content,
        "sources": [doc.page_content for doc in docs]
    }