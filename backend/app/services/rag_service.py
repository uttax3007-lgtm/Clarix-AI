import json, os
import faiss
from ..config import settings

_model = None
def _embedder():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")  # covers Hindi/Marathi
    return _model

def _dir(doc_id: str) -> str:
    d = os.path.join(settings.storage_dir, "index", doc_id)
    os.makedirs(d, exist_ok=True)
    return d

def build_index(doc_id: str, chunks: list[dict]):
    vecs = _embedder().encode([c["text"] for c in chunks], normalize_embeddings=True).astype("float32")
    idx = faiss.IndexFlatIP(vecs.shape[1]); idx.add(vecs)
    faiss.write_index(idx, os.path.join(_dir(doc_id), "faiss.index"))
    with open(os.path.join(_dir(doc_id), "chunks.json"), "w") as f:
        json.dump(chunks, f)

def retrieve(doc_id: str, query: str, k: int = 5) -> list[dict]:
    d = _dir(doc_id)
    idx = faiss.read_index(os.path.join(d, "faiss.index"))
    with open(os.path.join(d, "chunks.json")) as f:
        chunks = json.load(f)
    q = _embedder().encode([query], normalize_embeddings=True).astype("float32")
    scores, ids = idx.search(q, min(k, len(chunks)))
    return [{**chunks[i], "score": float(s)} for s, i in zip(scores[0], ids[0]) if i >= 0]
