"""
memory/user_store.py

Stage 2 — Long-Term User Memory
Remembers user preferences, recurring requirements, and project context across conversations.
Uses LangGraph Store (InMemoryStore with namespaced keys; pluggable for persistent backend).
Includes explicit rules for saving, updating, and deleting memories.
"""

from typing import Dict, Any, List, Optional
from langgraph.store.memory import InMemoryStore


class UserMemoryStore:
    """Manages cross-session user profile, recurring constraints, and project context."""

    def __init__(self, store: Optional[InMemoryStore] = None):
        self.store = store or InMemoryStore()

    def _get_namespace(self, user_id: str, category: str = "preferences") -> tuple:
        return ("users", str(user_id), category)

    def save_preference(self, user_id: str, key: str, value: Any, description: str = "") -> None:
        """Rule: Explicitly save or update a user preference (e.g. language, framework, styling)."""
        namespace = self._get_namespace(user_id, "preferences")
        payload = {
            "value": value,
            "description": description or key
        }
        self.store.put(namespace, key, payload)

    def get_preference(self, user_id: str, key: str) -> Optional[Any]:
        """Retrieves a specific preference by key."""
        namespace = self._get_namespace(user_id, "preferences")
        item = self.store.get(namespace, key)
        if item and hasattr(item, "value"):
            val = item.value
            return val.get("value") if isinstance(val, dict) else val
        return None

    def get_all_preferences(self, user_id: str) -> Dict[str, Any]:
        """Retrieves all active preferences and recurring requirements for a user."""
        namespace = self._get_namespace(user_id, "preferences")
        results = {}
        try:
            items = self.store.search(namespace)
            for item in items:
                key = item.key if hasattr(item, "key") else str(item)
                val = item.value if hasattr(item, "value") else item
                if isinstance(val, dict) and "value" in val:
                    results[key] = val["value"]
                else:
                    results[key] = val
        except Exception:
            pass
        return results

    def save_project_context(self, user_id: str, project_name: str, context_summary: str) -> None:
        """Rule: Remember long-term architectural rules or constraints for a specific project."""
        namespace = self._get_namespace(user_id, "projects")
        self.store.put(namespace, project_name, {"summary": context_summary})

    def get_project_context(self, user_id: str, project_name: str) -> Optional[str]:
        """Fetches stored project-level context."""
        namespace = self._get_namespace(user_id, "projects")
        item = self.store.get(namespace, project_name)
        if item and hasattr(item, "value") and isinstance(item.value, dict):
            return item.value.get("summary")
        return None

    def delete_memory(self, user_id: str, key: str, category: str = "preferences") -> bool:
        """Rule: Explicit deletion of out-of-date preferences or contexts."""
        namespace = self._get_namespace(user_id, category)
        try:
            self.store.delete(namespace, key)
            return True
        except Exception:
            return False

    def format_user_prompt_context(self, user_id: str = "default_user") -> str:
        """Formats long-term memory into an injectable context snippet for agent prompts."""
        prefs = self.get_all_preferences(user_id)
        if not prefs:
            return ""

        formatted = ["User Preferences & Recurring Constraints:"]
        for k, v in prefs.items():
            formatted.append(f"- {k}: {v}")
        return "\n".join(formatted)


# Singleton user store for Stage 2
user_memory_store = UserMemoryStore()
