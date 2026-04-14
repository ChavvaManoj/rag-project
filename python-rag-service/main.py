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
# 🧠 Chat Memory (simple)
# -------------------------------
chat_history = []

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
def chunk_text(text, chunk_size=300, overlap=50):
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
    metadatas = [
    {
        "source": safe_filename,
        "chunk_id": i
    }
    for i in range(len(chunks))
    ]

    vector_store.add_texts(chunks, metadatas=metadatas)

    print("🧬 Stored embeddings in ChromaDB")

    return {
        "message": "File processed and stored",
        "chunks": len(chunks)
    }


def keyword_search(query, docs):
    results = []
    query_lower = query.lower()

    for doc in docs:
        if query_lower in doc.page_content.lower():
            results.append(doc)
    
    return results


def simple_rerank(query, docs):
    scored = []

    query_Wprds = set(query.lower().split())

    for doc in docs:
        doc_words = set(doc.page_content.lower().split())
        score = len(query_Wprds.intersection(doc_words))
        scored.append((score, doc))
    
    scored.sort(reverse=True, key=lambda x: x[0])

    return [doc for _, doc in scored]

# -------------------------------
# 🔍 Query API
# -------------------------------
class QueryRequest(BaseModel):
    query: str



@app.post("/query")
async def query_rag(request: QueryRequest):

    query = request.query

    print("🔍 Query received:", query)

    #vector search
    vector_docs = vector_store.similarity_search(query, k=3)

    #Keyword search
    keyword_docs = keyword_search(query, vector_docs)

    #Merge + remove duplicates
    all_docs = vector_docs + keyword_docs

    #Deduplicate while preserving order
    unique_docs = list({doc.page_content: doc for doc in all_docs}.values())

    docs = simple_rerank(query, unique_docs)

    # take top 3 after reranking
    docs = docs[:3]


    context = "\n\n".join([doc.page_content for doc in docs])

    sources = [
    {
        "source": doc.metadata.get("source"),
        "chunk_id": doc.metadata.get("chunk_id")
    }
    for doc in docs
    ]


    # Format chat history
    history_text = ""
    for chat in chat_history[-5:]:   # last 5 interactions
        history_text += f"User: {chat['question']}\nAssistant: {chat['answer']}\n"



    prompt = f"""
You are a strict AI assistant.

Rules:
1. Answer ONLY using the given context
2. Keep the answer SHORT (1-2 lines)
3. Do NOT add any extra knowledge or assumptions
4. Use wording similar to context
5. Do NOT add extra explanation
6. If unsure, say "I don't know"


Conversation History:
{history_text}

Context:
{context}

Question:
{query}
"""

    response = llm.invoke(prompt)

    answer = response.content

    #Save in chat history
    chat_history.append({
        "question": query,
        "answer": answer
    })

    sources_text =  [doc.page_content for doc in docs]

    print("chat_history:", chat_history)
    print("Chat history updated. Total interactions:", len(chat_history))

    #return response + sources
    return {
    "query": query,
    "answer": response.content,
    "sources": sources,
    "sources_text": sources_text
}