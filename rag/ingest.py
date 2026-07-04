"""RAG subsystem — corpus ingest pipeline.

Reads text files from rag/corpus/, chunks them semantically, embeds each chunk
using local bge-small (sentence-transformers), and upserts into the Supabase
``kb_chunks`` table (384-dim pgvector).

Usage:
    python -m rag.ingest                     # ingest all corpus files
    python -m rag.ingest --dry-run           # preview chunks, no DB write
    DEMO_MODE=true python -m rag.ingest      # skip DB write, dump fixture JSON

Run once to populate the knowledge base; re-run to refresh.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import time
from pathlib import Path
from typing import Any

import core.env  # noqa: F401  (loads .env)

CORPUS_DIR = Path(__file__).resolve().parent / "corpus"
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))
CHUNK_SIZE = 400          # target tokens per chunk (approximate via words)
CHUNK_OVERLAP = 80        # overlap words between consecutive chunks
TOP_K_DEFAULT = 5


# ---------------------------------------------------------------------------
# Sentence-Transformers embedder (local, no API key)
# ---------------------------------------------------------------------------

_embed_model = None


def _get_embed_model():
    global _embed_model
    if _embed_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            model_name = "BAAI/bge-small-en-v1.5"
            print(f"[ingest] Loading embedding model: {model_name} ...")
            _embed_model = SentenceTransformer(model_name)
        except ImportError:
            print("[ingest] sentence-transformers not installed; using deterministic hash embeddings.")
            _embed_model = False
    return _embed_model


def _hash_embed(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    vec = [0.0] * dim
    for token in text.lower().split():
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        idx = int.from_bytes(digest[:4], "little") % dim
        sign = 1.0 if digest[4] & 1 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def embed(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Returns list of float vectors."""
    model = _get_embed_model()
    if model is False:
        return [_hash_embed(text) for text in texts]
    vecs = model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
    return [v.tolist() for v in vecs]


# ---------------------------------------------------------------------------
# Text chunking
# ---------------------------------------------------------------------------

def _split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Simple word-count-based sliding-window chunker that respects paragraph boundaries."""
    # Split by paragraph boundaries first
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks: list[str] = []
    current_words: list[str] = []

    for para in paragraphs:
        para_words = para.split()
        if len(current_words) + len(para_words) > chunk_size and current_words:
            chunks.append(" ".join(current_words))
            # keep overlap
            current_words = current_words[-overlap:]
        current_words.extend(para_words)

    if current_words:
        chunks.append(" ".join(current_words))

    return [c for c in chunks if len(c.strip()) > 50]


# ---------------------------------------------------------------------------
# Document loading
# ---------------------------------------------------------------------------

def _load_corpus_docs() -> list[dict]:
    """Load all .txt files from the corpus directory."""
    docs = []
    for path in sorted(CORPUS_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        # Extract document metadata from header lines
        lines = text.splitlines()
        title = path.stem.replace("_", " ").title()
        source_url = ""
        doc_id = path.stem

        for line in lines[:10]:
            if line.startswith("Source:"):
                source_url = line.split("Source:", 1)[1].strip()
            if line.startswith("Document ID:"):
                doc_id = line.split("Document ID:", 1)[1].strip()
            if line.startswith("# ") or (line.isupper() and len(line) > 10):
                title = line.lstrip("# ").strip()

        docs.append({
            "path": path,
            "text": text,
            "doc_id": doc_id,
            "title": title,
            "source_url": source_url,
        })

    return docs


# ---------------------------------------------------------------------------
# Main ingest
# ---------------------------------------------------------------------------

def ingest(dry_run: bool = False) -> list[dict]:
    """Ingest corpus → chunks → embeddings → Supabase (or dry-run/demo)."""
    docs = _load_corpus_docs()
    if not docs:
        print(f"[ingest] No .txt files found in {CORPUS_DIR}")
        return []

    all_chunks: list[dict] = []
    for doc in docs:
        chunks_text = _split_into_chunks(doc["text"])
        print(f"[ingest] {doc['path'].name}: {len(chunks_text)} chunks")
        for i, chunk in enumerate(chunks_text):
            chunk_id = hashlib.md5(f"{doc['doc_id']}:{i}:{chunk[:50]}".encode()).hexdigest()[:16]
            all_chunks.append({
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "source_url": doc["source_url"],
                "modality": "text",
                "chunk_text": chunk,
                "metadata": {
                    "chunk_index": i,
                    "total_chunks": len(chunks_text),
                    "file": doc["path"].name,
                    "chunk_id": chunk_id,
                },
            })

    print(f"[ingest] Total chunks: {len(all_chunks)} from {len(docs)} documents")

    if dry_run:
        for c in all_chunks[:3]:
            print(f"\n  [{c['doc_id']}] {c['chunk_text'][:120]}...")
        return all_chunks

    if DEMO_MODE:
        # Persist a fixture JSON for demo use (no embeddings needed)
        fixture_path = Path(__file__).resolve().parent.parent / "demo" / "fixtures" / "kb_chunks.json"
        records = [
            {k: v for k, v in c.items() if k != "embedding"}
            for c in all_chunks
        ]
        fixture_path.write_text(json.dumps(records[:20], indent=2, ensure_ascii=False))
        print(f"[ingest] DEMO_MODE: wrote {len(records[:20])} chunk stubs to {fixture_path}")
        return all_chunks

    # --- Embed and upsert ---
    texts = [c["chunk_text"] for c in all_chunks]
    print(f"[ingest] Embedding {len(texts)} chunks ...")
    t0 = time.time()
    vectors = embed(texts)
    print(f"[ingest] Embedded in {time.time() - t0:.1f}s")

    from core.supa import client
    db = client()

    # Batch upsert in groups of 100
    BATCH = 100
    upserted = 0
    for i in range(0, len(all_chunks), BATCH):
        batch = all_chunks[i : i + BATCH]
        rows: list[dict] = []
        for chunk, vec in zip(batch, vectors[i : i + BATCH]):
            row = {
                "doc_id": chunk["doc_id"],
                "title": chunk["title"],
                "source_url": chunk["source_url"],
                "modality": chunk["modality"],
                "chunk_text": chunk["chunk_text"],
                "embedding": vec,
                "metadata": chunk["metadata"],
            }
            rows.append(row)
        db.table("kb_chunks").upsert(rows).execute()
        upserted += len(rows)
        print(f"[ingest]  upserted {upserted}/{len(all_chunks)}")

    print(f"[ingest] Done. {upserted} chunks in Supabase.")
    return all_chunks


# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VayuNetra RAG ingest pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Preview chunks; do not write to DB")
    args = parser.parse_args()
    ingest(dry_run=args.dry_run)
