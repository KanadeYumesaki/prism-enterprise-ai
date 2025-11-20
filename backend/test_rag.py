import os
from dotenv import load_dotenv
from rag_kernel import HybridRetriever

# Load env for API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Skipping test: GEMINI_API_KEY not found.")
    exit(0)

print("Initializing HybridRetriever...")
rag = HybridRetriever(api_key)

# Test Data
text = "Prism is a governance AI system designed to ensure data privacy and policy compliance."
metadata = {"source": "test_doc"}

print(f"Adding document: {text}")
doc_id = rag.add_document(text, metadata)
print(f"Document added with ID: {doc_id}")

# Test Search
query = "What is Prism?"
print(f"Searching for: {query}")
results = rag.search(query)

print("\nSearch Results:")
for i, res in enumerate(results):
    print(f"{i+1}. {res}")

if any("Prism" in r for r in results):
    print("\n[SUCCESS] Found relevant document.")
else:
    print("\n[FAILURE] Did not find relevant document.")
