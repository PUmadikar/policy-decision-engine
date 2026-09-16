import re
from typing import List, Tuple
from rank_bm25 import BM25Okapi
from policy_engine.rag.indexer import PolicyChunk

class BM25Retriever:
    def __init__(self):
        self.bm25 = None
        self.chunks: List[PolicyChunk] = []

    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r'\w+', text.lower())
        return words

    def build_index(self, chunks: List[PolicyChunk]):
        self.chunks = chunks
        corpus = [self._tokenize(c.text) for c in chunks]
        self.bm25 = BM25Okapi(corpus)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[PolicyChunk, float]]:
        if self.bm25 is None or not self.chunks:
            return []
        
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((self.chunks[idx], float(scores[idx])))
        return results
