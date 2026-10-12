"""
memory/shared_memory.py

Unified 3-Stage Memory System:
  Stage 1 — Persistent Workflow Memory (LangGraph Checkpointer: thread states, approvals, retries)
  Stage 2 — Long-Term User Memory (LangGraph Store: preferences, recurring constraints)
  Stage 3 — Episodic & Semantic Retrieval (ChromaDB: past solutions, failures, verified research)
"""

from typing import Optional, Dict, Any

from memory.workflow_checkpoint import workflow_memory, WorkflowMemoryManager
from memory.user_store import user_memory_store, UserMemoryStore
from memory.episodic_memory import episodic_memory, EpisodicMemoryManager


class UnifiedMemoryFacade:
    """Unified access point coordinating the three memory stages across the multi-agent system."""

    def __init__(self):
        self.stage1_workflow = workflow_memory
        self.stage2_user = user_memory_store
        self.stage3_episodic = episodic_memory

    # --- Backward-compatible convenience methods ---
    def save_run(self, task: str, report: str, code: str = "", research_notes: str = "", success: bool = True):
        """Saves a completed execution into Stage 3 episodic memory."""
        self.stage3_episodic.save_episode(
            task=task,
            summary=report,
            code=code,
            research_notes=research_notes,
            success=success
        )

    def recall_past_runs(self, current_task: str, user_id: str = "default_user") -> str:
        """Combines Stage 2 user preferences with Stage 3 episodic past run retrieval for prompt injection."""
        context_parts = []

        # Stage 2: User preferences & recurring constraints
        user_prefs = self.stage2_user.format_user_prompt_context(user_id=user_id)
        if user_prefs:
            context_parts.append(user_prefs)

        # Stage 3: Episodic memory from similar past runs
        episodic_context = self.stage3_episodic.format_retrieved_context(current_task)
        if episodic_context:
            context_parts.append(episodic_context)

        return "\n\n".join(context_parts)


# Global singleton instance for backward compatibility
memory = UnifiedMemoryFacade()
