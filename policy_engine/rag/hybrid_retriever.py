import os
from typing import List, Dict, Tuple
from policy_engine.rag.indexer import PolicyIndexer, PolicyChunk
from policy_engine.rag.vectorstore import FAISSVectorStore
from policy_engine.rag.bm25_retriever import BM25Retriever
from policy_engine.config import settings

class HybridRetriever:
    def __init__(self, pdf_path: str = settings.POLICY_PDF_PATH, index_dir: str = settings.INDEX_DIR):
        self.pdf_path = pdf_path
        self.index_dir = index_dir
        self.indexer = PolicyIndexer(pdf_path)
        self.chunks = self.indexer.load_and_chunk()
        
        self.dense_store = FAISSVectorStore(settings.EMBEDDING_MODEL_NAME)
        
        faiss_file = os.path.join(index_dir, "faiss.index")
        meta_file = os.path.join(index_dir, "chunks_metadata.json")
        
        if os.path.exists(faiss_file) and os.path.exists(meta_file):
            try:
                self.dense_store.load(index_dir)
                self.chunks = self.dense_store.chunks
            except Exception as e:
                self.dense_store.build_index(self.chunks)
                self.dense_store.save(index_dir)
        else:
            self.dense_store.build_index(self.chunks)
            self.dense_store.save(index_dir)
        
        self.sparse_store = BM25Retriever()
        self.sparse_store.build_index(self.chunks)

    def retrieve(
        self,
        query: str,
        top_k: int = settings.HYBRID_TOP_K,
        rrf_k: int = 60
    ) -> List[Tuple[PolicyChunk, float]]:
        dense_results = self.dense_store.search(query, top_k=top_k * 2)
        sparse_results = self.sparse_store.search(query, top_k=top_k * 2)

        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, PolicyChunk] = {}

        for rank, (chunk, score) in enumerate(dense_results):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank + 1))

        for rank, (chunk, score) in enumerate(sparse_results):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank + 1))

        sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)
        
        scored_candidates = []
        for cid in sorted_cids[:top_k * 2]:
            chunk = chunk_map[cid]
            base_score = rrf_scores[cid]
            
            q_terms = [w.lower() for w in query.split() if len(w) > 3]
            matches = sum(1 for term in q_terms if term in chunk.text.lower())
            final_score = base_score + (matches * 0.005)
            
            scored_candidates.append((chunk, final_score))

        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        return scored_candidates[:top_k]

if __name__ == "__main__":
    retriever = HybridRetriever()
    q = "room rent cap limit initial waiting period cataract pre-existing"
    results = retriever.retrieve(q, top_k=5)
    print(f"Hybrid retrieval returned {len(results)} results for query: '{q}'")
    for chunk, score in results:
        print(f"[{chunk.chunk_id}] (Score: {score:.4f}) Page {chunk.page} | Section: {chunk.section}\n{chunk.text[:150]}...\n")
