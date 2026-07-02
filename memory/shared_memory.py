"""
memory/shared_memory.py

Long-term memory using ChromaDB.
We store previous tasks and final reports so the agents can recall past experiences.
"""

import hashlib
import os
import re
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from chromadb.config import Settings


class SimpleEmbeddingFunction(EmbeddingFunction[Documents]):
    """A lightweight embedding function that avoids downloading model files."""

    def __call__(self, input: Documents) -> Embeddings:
        vectors = []
        for text in input:
            tokens = re.findall(r"\w+", (text or "").lower())
            vector = [0.0] * 8
            for token in tokens:
                index = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % len(vector)
                vector[index] += 1.0

            norm = sum(value * value for value in vector) ** 0.5
            if norm:
                vector = [value / norm for value in vector]

            vectors.append(vector)

        return vectors


class LongTermMemory:
    def __init__(self, db_path: str = "./chroma_db"):
        self.db_path = db_path
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        try:
            self.client.delete_collection(name="agent_runs")
        except Exception:
            pass

        self.collection = self.client.get_or_create_collection(
            name="agent_runs",
            metadata={"hnsw:space": "cosine"},
            embedding_function=SimpleEmbeddingFunction(),
        )

    def save_run(self, task: str, report: str):
        """Save a completed task and its report to the vector database."""
        # Use the task as the document ID, or generate a random one. 
        # Using hash of task for simplicity.
        doc_id = str(hash(task))
        
        # We store the task + report as the document text to embed, 
        # and attach the task as metadata.
        text_to_embed = f"Task: {task}\n\nReport: {report}"
        
        self.collection.upsert(
            documents=[text_to_embed],
            metadatas=[{"task": task}],
            ids=[doc_id]
        )
        print(f"[Memory] Saved run to ChromaDB. Task: {task[:50]}...")

    def recall_past_runs(self, current_task: str, n_results: int = 1) -> str:
        """Query the vector database for similar past tasks."""
        if self.collection.count() == 0:
            return ""
            
        results = self.collection.query(
            query_texts=[current_task],
            n_results=min(n_results, self.collection.count())
        )
        
        if not results["documents"] or not results["documents"][0]:
            return ""
            
        retrieved_docs = results["documents"][0]
        
        # Format the context
        context = "Here are some similar tasks you've completed in the past:\n\n"
        for idx, doc in enumerate(retrieved_docs):
            context += f"--- Past Run {idx+1} ---\n{doc}\n\n"
            
        return context

# Singleton instance
memory = LongTermMemory()
