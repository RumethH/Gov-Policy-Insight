import sqlite3
import json
import numpy as np
from typing import Optional, Dict, Any, List
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class SemanticCache:
    def __init__(self, db_path: str = "cache.sqlite", threshold: float = 0.95):
        self.db_path = db_path
        self.threshold = threshold
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS semantic_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT,
                    query_embedding BLOB,
                    response_json TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

    def get(self, query: str, query_embedding: Optional[List[float]] = None) -> Optional[Dict[str, Any]]:
        if query_embedding is not None:
            query_vec = np.array(query_embedding)
        else:
            query_vec = np.array(self.embeddings.embed_query(query))
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT query, query_embedding, response_json FROM semantic_cache")
            rows = cursor.fetchall()
            
            best_match = None
            max_sim = -1.0
            
            for row_query, row_emb_blob, row_resp in rows:
                row_vec = np.frombuffer(row_emb_blob, dtype=np.float64)
                sim = self._cosine_similarity(query_vec, row_vec)
                
                if sim > max_sim:
                    max_sim = sim
                    best_match = row_resp
            
            if max_sim >= self.threshold:
                return json.loads(best_match)
        return None

    def set(self, query: str, response: Dict[str, Any], query_embedding: Optional[List[float]] = None):
        if query_embedding is not None:
            query_vec = np.array(query_embedding, dtype=np.float64)
        else:
            query_vec = np.array(self.embeddings.embed_query(query), dtype=np.float64)
            
        response_json = json.dumps(response)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO semantic_cache (query, query_embedding, response_json) VALUES (?, ?, ?)",
                (query, query_vec.tobytes(), response_json)
            )
            conn.commit()
