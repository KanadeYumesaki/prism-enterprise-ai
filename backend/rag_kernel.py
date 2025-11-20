import os
import sqlite3
import chromadb
from chromadb.config import Settings
from google import genai
from google.genai import types
from typing import List, Dict, Any
import uuid
from rank_bm25 import BM25Okapi

# [EDUCATIONAL COMMENT]
# ChromaDB has two main client types:
# 1. EphemeralClient: Stores data in memory. Fast for testing, but data is lost when the process ends.
# 2. PersistentClient: Stores data on disk (e.g., in a folder). Data survives restarts.
# Here we use PersistentClient to ensure our RAG knowledge base persists.

class EmbeddingService:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = "models/text-embedding-004"

    def embed_text(self, text: str) -> List[float]:
        """Generates embedding for a single string."""
        result = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=768) # Standard size
        )
        return result.embeddings[0].values

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a list of strings."""
        # Note: For large batches, you might want to chunk this.
        # This simple implementation iterates, but batch APIs are better if available.
        return [self.embed_text(t) for t in texts]

class VectorStore:
    def __init__(self, persist_path: str = "./chroma_db"):
        # Initialize persistent client
        self.client = chromadb.PersistentClient(path=persist_path)
        
        # Get or create a collection. Collections are like tables in a relational DB.
        self.collection = self.client.get_or_create_collection(name="governance_docs")

    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str], embeddings: List[List[float]]):
        """Adds documents to the vector store."""
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings
        )

    def search_similarity(self, query_embedding: List[float], n_results: int = 5) -> Dict[str, Any]:
        """Searches for similar documents using vector similarity."""
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

    def list_documents(self) -> List[Dict[str, Any]]:
        """Lists all documents in the collection."""
        # ChromaDB's get() returns all items if no ids are specified
        results = self.collection.get()
        
        docs = []
        if results['ids']:
            for i, doc_id in enumerate(results['ids']):
                meta = results['metadatas'][i] if results['metadatas'] else {}
                # Ensure metadata is a dict
                if meta is None:
                    meta = {}
                docs.append({
                    "id": doc_id,
                    "metadata": meta
                })
        return docs

class KeywordStore:
    def __init__(self, db_path: str = "governance_logs.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Simple full-text search setup using a standard table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keyword_docs (
                id TEXT PRIMARY KEY,
                content TEXT,
                metadata TEXT
            )
        """)
        conn.commit()
        conn.close()

    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        data = []
        for doc, meta, doc_id in zip(documents, metadatas, ids):
            data.append((doc_id, doc, str(meta)))
        
        cursor.executemany("INSERT OR REPLACE INTO keyword_docs (id, content, metadata) VALUES (?, ?, ?)", data)
        conn.commit()
        conn.close()

    def search_keyword(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Performs a simple keyword search using SQL LIKE.
        For production, consider FTS5 (SQLite) or a dedicated search engine.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Simple token-based OR search
        tokens = query.split()
        if not tokens:
            return []

        # Construct a query that checks if any token is present
        # This is a naive implementation for demonstration.
        like_clauses = " OR ".join(["content LIKE ?" for _ in tokens])
        params = [f"%{token}%" for token in tokens]
        
        sql = f"SELECT * FROM keyword_docs WHERE {like_clauses} LIMIT ?"
        params.append(n_results)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                "id": row["id"],
                "document": row["content"],
                "metadata": row["metadata"] # Note: This is a string representation
            })
        return results

class HybridRetriever:
    def __init__(self, api_key: str):
        self.embedding_service = EmbeddingService(api_key)
        self.vector_store = VectorStore()
        self.keyword_store = KeywordStore()

    def add_document(self, text: str, metadata: Dict[str, Any] = None):
        if metadata is None:
            metadata = {}
        
        doc_id = str(uuid.uuid4())
        embedding = self.embedding_service.embed_text(text)
        
        # Add to Vector Store
        self.vector_store.add_documents(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id],
            embeddings=[embedding]
        )
        
        # Add to Keyword Store
        self.keyword_store.add_documents(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )
        return doc_id

    def search(self, query: str, n_results: int = 5) -> List[str]:
        # 1. Vector Search
        query_embedding = self.embedding_service.embed_text(query)
        vector_results = self.vector_store.search_similarity(query_embedding, n_results)
        
        # Extract documents from vector results
        # vector_results['documents'] is a list of lists (one list per query)
        v_docs = vector_results['documents'][0] if vector_results['documents'] else []
        
        # 2. Keyword Search
        keyword_results = self.keyword_store.search_keyword(query, n_results)
        k_docs = [r['document'] for r in keyword_results]
        
        # 3. Hybrid Fusion (Simple Union for now)
        # In a more advanced system, we would use Reciprocal Rank Fusion (RRF)
        all_docs = list(set(v_docs + k_docs))
        
        return all_docs[:n_results]

    def list_documents(self) -> List[Dict[str, Any]]:
        return self.vector_store.list_documents()
