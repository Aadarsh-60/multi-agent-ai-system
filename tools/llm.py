"""
tools/llm.py

One place to create the LLM so every agent calls the model
the exact same way. Keeps the agent files short and simple.
"""

import os
from langchain_groq import ChatGroq


class GroqFallbackWrapper:
    """Wraps the LangChain model (with its built-in fallbacks) to apply newline cleanup."""

    def __init__(self, inner_model):
        self.inner_model = inner_model

    def invoke(self, prompt: str):
        import re
        response = self.inner_model.invoke(prompt)
        if hasattr(response, "content") and isinstance(response.content, str):
            response.content = re.sub(r'\n{3,}', '\n\n', response.content.strip())
        return response

    def stream(self, prompt: str):
        newline_count = 0
        for chunk in self.inner_model.stream(prompt):
            if hasattr(chunk, "content") and isinstance(chunk.content, str):
                filtered_content = ""
                for char in chunk.content:
                    if char == '\n':
                        newline_count += 1
                        if newline_count <= 2:
                            filtered_content += char
                    else:
                        newline_count = 0
                        filtered_content += char
                if filtered_content:
                    yield filtered_content


def get_llm(temperature: float = 0.3):
    """Returns a ready-to-use chat model with automatic multi-model failover."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found! Please make sure you have created a .env file "
            "(you can rename .env.example) and added your Groq API key."
        )

    # 1. Primary Model
    primary_llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=temperature,
        groq_api_key=api_key,
        streaming=True
    )
    
    # 2. First Fallback Model (If primary hits quota/rate limits)
    fallback_1 = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=temperature,
        groq_api_key=api_key,
        streaming=True
    )
    
    # 3. Second Fallback Model (If both fail)
    fallback_2 = ChatGroq(
        model="mixtral-8x7b-32768",
        temperature=temperature,
        groq_api_key=api_key,
        streaming=True
    )

    # LangChain natively handles the try-catch for API errors and failover
    model_with_fallbacks = primary_llm.with_fallbacks([fallback_1, fallback_2])
    
    return GroqFallbackWrapper(model_with_fallbacks)
