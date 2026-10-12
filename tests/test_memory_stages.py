"""
tests/test_memory_stages.py

Comprehensive tests for the 3-Stage Memory Architecture:
  Stage 1: Persistent workflow memory (LangGraph checkpointer)
  Stage 2: Long-term user memory (LangGraph Store)
  Stage 3: Episodic and semantic retrieval (ChromaDB vector store)
"""

import unittest
from memory.workflow_checkpoint import workflow_memory, WorkflowMemoryManager
from memory.user_store import user_memory_store, UserMemoryStore
from memory.episodic_memory import episodic_memory, EpisodicMemoryManager
from memory.shared_memory import memory


class TestThreeStageMemory(unittest.TestCase):

    # ── Stage 1: Persistent Workflow Memory ──
    def test_stage1_workflow_checkpointer(self):
        """Test LangGraph checkpointer initialization and thread configuration."""
        self.assertIsNotNone(workflow_memory.checkpointer)
        cfg = workflow_memory.get_thread_config("test_thread_123")
        self.assertEqual(cfg["configurable"]["thread_id"], "test_thread_123")

    # ── Stage 2: Long-Term User Memory ──
    def test_stage2_user_store_lifecycle(self):
        """Test rules for saving, retrieving, formatting, and deleting user preferences."""
        store = UserMemoryStore()
        user_id = "developer_alice"

        # 1. Save preferences
        store.save_preference(user_id, "framework", "FastAPI", description="Preferred backend framework")
        store.save_preference(user_id, "style", "PEP8 with type hints", description="Code formatting standard")

        # 2. Retrieve single & all
        self.assertEqual(store.get_preference(user_id, "framework"), "FastAPI")
        all_prefs = store.get_all_preferences(user_id)
        self.assertIn("framework", all_prefs)
        self.assertIn("style", all_prefs)

        # 3. Format prompt context
        prompt_ctx = store.format_user_prompt_context(user_id)
        self.assertIn("FastAPI", prompt_ctx)
        self.assertIn("PEP8", prompt_ctx)

        # 4. Project context
        store.save_project_context(user_id, "auth_service", "Uses JWT with RSA256 tokens")
        proj_ctx = store.get_project_context(user_id, "auth_service")
        self.assertEqual(proj_ctx, "Uses JWT with RSA256 tokens")

        # 5. Delete preference
        deleted = store.delete_memory(user_id, "framework")
        self.assertTrue(deleted)
        self.assertIsNone(store.get_preference(user_id, "framework"))

    # ── Stage 3: Episodic & Semantic Retrieval ──
    def test_stage3_episodic_memory(self):
        """Test storing and semantically retrieving episodes with metadata filtering."""
        doc_id = episodic_memory.save_episode(
            task="Build a robust rate limiter",
            summary="Implemented token bucket algorithm in Python",
            code="class TokenBucket: pass",
            research_notes="Token bucket guarantees smooth traffic shaping",
            success=True,
            category="networking"
        )
        self.assertTrue(len(doc_id) > 0)

        # Retrieve with metadata filter
        results = episodic_memory.retrieve_similar_episodes(
            query="rate limiter token bucket",
            filter_metadata={"category": "networking"},
            n_results=1
        )
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]["metadata"]["category"], "networking")

        # Format context
        ctx = episodic_memory.format_retrieved_context("rate limiter")
        self.assertIn("TokenBucket", ctx)

    # ── Unified Facade ──
    def test_unified_facade_integration(self):
        """Test unified memory facade delegating across stages."""
        memory.stage2_user.save_preference("default_user", "preferred_tool", "BeautifulSoup")
        memory.save_run(
            task="Scrape news headlines",
            report="Completed web scraping script using BeautifulSoup",
            code="import requests; from bs4 import BeautifulSoup"
        )

        recalled = memory.recall_past_runs("Scrape news headlines", user_id="default_user")
        self.assertIn("BeautifulSoup", recalled)


if __name__ == "__main__":
    unittest.main()
