"""
tools/search_tool.py

Wraps the Tavily Search API so our Research Agent can search
the web for live / up-to-date information.

Get a free API key from https://tavily.com and put it in your .env
file as TAVILY_API_KEY.
"""

import os
from tavily import TavilyClient


def search_tool(query: str, max_results: int = 5) -> str:
    """
    Runs a Tavily web search and returns the results
    as one readable text block (easy for the LLM to read).
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "TAVILY_API_KEY is missing. Please add it to your .env file."

    client = TavilyClient(api_key=api_key)

    response = client.search(
        query=query,
        max_results=max_results,
        search_depth="advanced",
    )

    # turn the raw results into a simple text block
    results_text = ""
    for i, result in enumerate(response.get("results", []), start=1):
        results_text += f"\n{i}. {result['title']}\n"
        results_text += f"   URL: {result['url']}\n"
        results_text += f"   Summary: {result['content']}\n"

    if not results_text:
        results_text = "No results found."

    return results_text


# quick manual test -> run: python tools/search_tool.py
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    print(search_tool("latest AI agent frameworks 2026"))
