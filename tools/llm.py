"""
tools/llm.py

One place to create the LLM so every agent calls the model
the exact same way. Keeps the agent files short and simple.
"""

import os
from langchain_groq import ChatGroq


class GroqFallbackWrapper:
    """Wraps the Groq client and falls back to a simple response on quota errors."""

    def __init__(self, inner_model):
        self.inner_model = inner_model

    def invoke(self, prompt: str):
        try:
            import re
            response = self.inner_model.invoke(prompt)
            if hasattr(response, "content") and isinstance(response.content, str):
                response.content = re.sub(r'\n{3,}', '\n\n', response.content.strip())
            return response

    def stream(self, prompt: str):
        try:
            for chunk in self.inner_model.stream(prompt):
                if hasattr(chunk, "content") and isinstance(chunk.content, str):
                    yield chunk.content
        except Exception as exc:
            message = str(exc)
            if "RESOURCE_EXHAUSTED" in message or "quota" in message.lower() or "429" in message:
                yield self._fallback_response(prompt)
            else:
                raise
        except Exception as exc:
            message = str(exc)
            if "RESOURCE_EXHAUSTED" in message or "quota" in message.lower() or "429" in message:
                return type("FallbackResponse", (), {"content": self._fallback_response(prompt)})()
            raise

    @staticmethod
    def _fallback_response(prompt: str) -> str:
        if "planner" in prompt.lower():
            return (
                "Fallback plan: 1. Define the problem and success criteria. "
                "2. Gather relevant context and examples. "
                "3. Implement a simple initial solution. "
                "4. Test and refine the result."
            )
        if "research" in prompt.lower():
            return "Fallback research summary: The model quota is temporarily exhausted, so this run uses a concise placeholder summary and should be retried once the quota resets."
        if "coding" in prompt.lower():
            return "Fallback code: # Quota exhausted; please retry later.\nprint('Quota exhausted; retry once the model is available.')"
        if "review" in prompt.lower():
            return "Fallback review: The review step could not be completed because the model quota is currently exhausted."
        return "Fallback response: the model quota is currently exhausted. Please retry once the provider allows more requests."


def get_llm(temperature: float = 0.3):
    """Returns a ready-to-use chat model."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found! Please make sure you have created a .env file "
            "(you can rename .env.example) and added your Groq API key."
        )

    inner_model = ChatGroq(
        model="openai/gpt-oss-120b",  # Updated to a model accessible with current API key
        temperature=temperature,
        groq_api_key=api_key,
        streaming=True
    )
    return GroqFallbackWrapper(inner_model)
