"""
memory/episodic_memory.py

Stage 3 — Episodic and Semantic Retrieval
Retrieves relevant past task summaries, successful solutions, failed attempts, and verified research.
Built on ChromaDB vector store with rich metadata filters, access controls, and cosine similarity ranking.
"""

import hashlib
import re
import time
from typing import Dict, Any, List, Optional
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from chromadb.config import Settings


class LightweightEmbeddingFunction(EmbeddingFunction[Documents]):
    """Lightweight deterministic feature embedding for vector retrieval without heavy weights."""

    def __call__(self, input: Documents) -> Embeddings:
        vectors = []
        for text in input:
            tokens = re.findall(r"\w+", (text or "").lower())
            vector = [0.0] * 16
            for token in tokens:
                idx = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % len(vector)
                vector[idx] += 1.0

            norm = sum(v * v for v in vector) ** 0.5
            if norm:
                vector = [v / norm for v in vector]
            vectors.append(vector)
        return vectors


class EpisodicMemoryManager:
    """Stores and retrieves historical episodes (successes, failures, verified research) with metadata filters."""

    def __init__(self, db_path: str = "./chroma_db"):
        self.db_path = db_path
        self._init_client()

    def _init_client(self):
        """Initializes ChromaDB with self-healing fallback for cross-version SQLite compatibility."""
        try:
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(
                name="episodic_runs",
                metadata={"hnsw:space": "cosine"},
                embedding_function=LightweightEmbeddingFunction(),
            )
            # Verify collection integrity
            _ = self.collection.count()
        except Exception as e:
            print(f"[Warning] ChromaDB persistent client error: {e}. Falling back to EphemeralClient.")
            try:
                self.client = chromadb.EphemeralClient(
                    settings=Settings(anonymized_telemetry=False)
                )
                self.collection = self.client.get_or_create_collection(
                    name="episodic_runs",
                    metadata={"hnsw:space": "cosine"},
                    embedding_function=LightweightEmbeddingFunction(),
                )
            except Exception as e2:
                print(f"[Warning] Failed to initialize fallback ChromaDB: {e2}")
                self.client = None
                self.collection = None

    def save_episode(
        self,
        task: str,
        summary: str,
        code: str = "",
        research_notes: str = "",
        success: bool = True,
        category: str = "general",
        user_id: str = "default_user"
    ) -> str:
        """Stores an execution episode with structured metadata for semantic retrieval."""
        if not self.collection:
            return ""

        doc_id = hashlib.sha256(f"{task}_{time.time()}".encode("utf-8")).hexdigest()[:16]

        document_content = (
            f"TASK: {task}\n"
            f"SUMMARY: {summary}\n"
            f"RESEARCH: {research_notes[:2000]}\n"
            f"CODE SOLUTION:\n{code[:3000]}"
        )

        metadata = {
            "task": task[:200],
            "success": bool(success),
            "category": str(category),
            "user_id": str(user_id),
            "timestamp": int(time.time()),
            "has_code": bool(code.strip())
        }

        try:
            self.collection.upsert(
                documents=[document_content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            return doc_id
        except Exception as e:
            print(f"[Warning] Failed to save episode to ChromaDB: {e}")
            return ""

    def retrieve_similar_episodes(
        self,
        query: str,
        filter_metadata: Optional[Dict[str, Any]] = None,
        n_results: int = 2
    ) -> List[Dict[str, Any]]:
        """Queries the vector database for similar past tasks with optional metadata filters."""
        if not self.collection:
            return []

        try:
            total_count = self.collection.count()
            if total_count == 0:
                return []

            query_kwargs = {
                "query_texts": [query],
                "n_results": min(n_results, total_count)
            }

            if filter_metadata:
                query_kwargs["where"] = filter_metadata

            results = self.collection.query(**query_kwargs)
            episodes = []

            if results.get("documents") and results["documents"][0]:
                docs = results["documents"][0]
                metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                for doc, meta in zip(docs, metas):
                    episodes.append({
                        "content": doc,
                        "metadata": meta
                    })

            return episodes
        except Exception as e:
            print(f"[Warning] ChromaDB retrieve_similar_episodes failed: {e}")
            return []

    def format_retrieved_context(self, query: str, filter_metadata: Optional[Dict[str, Any]] = None) -> str:
        """Helper to format retrieved similar runs into a clean markdown section for Planner & Coder."""
        try:
            episodes = self.retrieve_similar_episodes(query, filter_metadata=filter_metadata, n_results=2)
            if not episodes:
                return ""

            context_lines = ["--- Episodic Context from Past Runs ---"]
            for idx, ep in enumerate(episodes, 1):
                status = "Verified Success" if ep["metadata"].get("success", True) else "Failed Attempt"
                context_lines.append(f"Episode {idx} [{status}]:\n{ep['content']}\n")
            return "\n".join(context_lines)
        except Exception as e:
            print(f"[Warning] Failed to format retrieved context: {e}")
            return ""


# Singleton episodic memory for Stage 3
episodic_memory = EpisodicMemoryManager()
