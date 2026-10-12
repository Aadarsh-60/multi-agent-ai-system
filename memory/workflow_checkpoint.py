"""
memory/workflow_checkpoint.py

Stage 1 — Persistent Workflow Memory
Preserves messages, state, human approval status, and retry counts across execution steps.
Uses LangGraph's native checkpointer (InMemorySaver for local runtimes, pluggable for PostgreSQL/SQLite in production).
"""

from typing import Optional, Any, Dict
from langgraph.checkpoint.memory import MemorySaver


class WorkflowMemoryManager:
    """Manages thread-level workflow checkpoints and state persistence."""

    def __init__(self, checkpointer: Optional[Any] = None):
        self._checkpointer = checkpointer or MemorySaver()

    @property
    def checkpointer(self) -> Any:
        """Returns the active LangGraph checkpointer instance."""
        return self._checkpointer

    def get_thread_config(self, thread_id: str) -> Dict[str, Any]:
        """Creates a standard LangGraph execution config keyed by thread ID."""
        return {
            "configurable": {
                "thread_id": str(thread_id)
            }
        }


# Singleton workflow checkpointer for Stage 1
workflow_memory = WorkflowMemoryManager()
