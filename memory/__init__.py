"""
memory package for AgentMind.

Structured 3-Stage Memory Architecture:
  Stage 1: Persistent Workflow Memory (WorkflowMemoryManager, workflow_memory)
  Stage 2: Long-Term User Memory (UserMemoryStore, user_memory_store)
  Stage 3: Episodic and Semantic Retrieval (EpisodicMemoryManager, episodic_memory)
"""

from memory.workflow_checkpoint import WorkflowMemoryManager, workflow_memory
from memory.user_store import UserMemoryStore, user_memory_store
from memory.episodic_memory import EpisodicMemoryManager, episodic_memory
from memory.shared_memory import UnifiedMemoryFacade, memory

__all__ = [
    # Stage 1
    "WorkflowMemoryManager",
    "workflow_memory",
    # Stage 2
    "UserMemoryStore",
    "user_memory_store",
    # Stage 3
    "EpisodicMemoryManager",
    "episodic_memory",
    # Unified Facade
    "UnifiedMemoryFacade",
    "memory",
]
