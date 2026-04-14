from dotenv import load_dotenv
import os

load_dotenv()   # ✅ MUST be before anything else

print("API KEY:", os.getenv("OPENAI_API_KEY"))  # debug

import requests
import json

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import Faithfulness, AnswerRelevancy
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()

# Load dataset
with open("eval_data.json", "r") as f:
    data = json.load(f)

questions = []
answers = []
contexts = []

# Call API
for item in data:
    query = item["question"]

    response = requests.post(
        "http://localhost:8000/query",
        json={"query": query}
    )

    result = response.json()

    # Debug print (optional but useful)
    print("API Response:", result)

    questions.append(query)
    answers.append(result["answer"])

    # ✅ FIXED
    contexts.append(result["sources_text"])

# Convert dataset
dataset = Dataset.from_dict({
    "question": questions,
    "answer": answers,
    "contexts": contexts
})

# Evaluate
result = evaluate(
    dataset,
    metrics=[Faithfulness(), AnswerRelevancy()],
    embeddings=embeddings
)

print("\n🔍 Evaluation Results:")
print(result)