import os
import json
import numpy as np
import faiss
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
from policy_engine.rag.indexer import PolicyChunk

class FAISSVectorStore:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.chunks: List[PolicyChunk] = []

    def build_index(self, chunks: List[PolicyChunk]):
        self.chunks = chunks
        texts = [c.text for c in chunks]
        embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        dimension = embeddings.shape[1]
        
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product for normalized vectors (Cosine similarity)
        self.index.add(embeddings.astype(np.float32))

    def search(self, query: str, top_k: int = 5) -> List[Tuple[PolicyChunk, float]]:
        if self.index is None or not self.chunks:
            return []
        
        query_vec = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        scores, indices = self.index.search(query_vec.astype(np.float32), top_k)
        
        results = []
        for idx, score in zip(indices[0], scores[0]):
            if 0 <= idx < len(self.chunks):
                results.append((self.chunks[idx], float(score)))
        return results

    def save(self, index_dir: str):
        os.makedirs(index_dir, exist_ok=True)
        faiss_path = os.path.join(index_dir, "faiss.index")
        meta_path = os.path.join(index_dir, "chunks_metadata.json")
        
        faiss.write_index(self.index, faiss_path)
        meta_data = [
            {
                "chunk_id": c.chunk_id,
                "page": c.page,
                "section": c.section,
                "sub_section": c.sub_section,
                "text": c.text
            }
            for c in self.chunks
        ]
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_data, f, indent=2, ensure_ascii=False)

    def load(self, index_dir: str):
        faiss_path = os.path.join(index_dir, "faiss.index")
        meta_path = os.path.join(index_dir, "chunks_metadata.json")
        
        if not os.path.exists(faiss_path) or not os.path.exists(meta_path):
            raise FileNotFoundError("FAISS index or metadata missing.")
            
        self.index = faiss.read_index(faiss_path)
        with open(meta_path, "r", encoding="utf-8") as f:
            meta_data = json.load(f)
            self.chunks = [PolicyChunk(**item) for item in meta_data]
