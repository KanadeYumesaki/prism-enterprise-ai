import requests
import os
from dotenv import load_dotenv

# Load env for API key (not strictly needed for this test but good practice)
load_dotenv()

BASE_URL = "http://localhost:8000"

def test_knowledge_api():
    print("Testing Knowledge Base API...")
    
    # 1. Ingest a file
    print("Ingesting test file...")
    files = {'file': ('test_kb_doc.txt', 'This is a test document for the Knowledge Base.')}
    response = requests.post(f"{BASE_URL}/ingest", files=files)
    
    if response.status_code == 200:
        print("[SUCCESS] Ingestion successful.")
        print(response.json())
    else:
        print(f"[FAILURE] Ingestion failed: {response.status_code}")
        print(response.text)
        return

    # 2. List documents
    print("Listing documents...")
    response = requests.get(f"{BASE_URL}/knowledge")
    
    if response.status_code == 200:
        docs = response.json()
        print(f"[SUCCESS] Retrieved {len(docs)} documents.")
        for doc in docs:
            print(f"- ID: {doc['id']}, Metadata: {doc['metadata']}")
            
        # Verify our document is there
        found = any(d['metadata'].get('filename') == 'test_kb_doc.txt' for d in docs)
        if found:
            print("[SUCCESS] Test document found in list.")
        else:
            print("[FAILURE] Test document NOT found in list.")
    else:
        print(f"[FAILURE] Listing failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    try:
        test_knowledge_api()
    except requests.exceptions.ConnectionError:
        print("[ERROR] Could not connect to backend. Make sure it is running on port 8000.")
