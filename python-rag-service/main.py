from fastapi import FastAPI, UploadFile, File
import shutil
import os

app = FastAPI()

# Health API
@app.get("/")
def health():
    return {"status": "Python RAG service running"}


# Create upload folder
UPLOAD_DIR = "uploaded_docs"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


# Ingestion API
@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):

    print("🔥 File received in Python:", file.filename)

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print("✅ File saved at:", file_path)

    return {
        "message": "File received",
        "file_path": file_path
    }