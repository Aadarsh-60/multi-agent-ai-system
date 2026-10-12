"""
graph/streaming.py

LangGraph Streaming & Structured Response Formatting:
  - Token streaming: Uses graph.astream() / graph.stream() with stream_mode="messages"
    to receive LLM message chunks progressively as they are generated.
  - Structured output: Formats responses with Markdown headings, lists, tables, and code blocks.
  - Final response: Accumulates the streamed chunks and stores the complete answer when generation finishes.
"""

from typing import Dict, Any, AsyncIterator, Iterator, Optional, Tuple
from langchain_core.runnables import RunnableConfig


async def astream_graph_tokens(
    graph,
    input_state: Dict[str, Any],
    config: Optional[RunnableConfig] = None
) -> AsyncIterator[Dict[str, Any]]:
    """
    Asynchronously streams LLM token chunks across LangGraph nodes using stream_mode="messages".

    Yields dictionaries:
      {
        "node": str,              # e.g. "planner", "coder", "reporter"
        "token": str,             # the current token chunk
        "accumulated": str,       # accumulated text for this node
        "is_final": bool,         # True on final node completion chunk
        "final_state": Optional[Dict]
      }
    """
    node_buffers: Dict[str, str] = {}
    current_node = None

    async for item in graph.astream(input_state, config=config, stream_mode="messages"):
        if isinstance(item, tuple) and len(item) == 2:
            msg, metadata = item
            node_name = metadata.get("langgraph_node", "unknown")
            token = getattr(msg, "content", "") if msg else ""
        else:
            msg = item
            node_name = "unknown"
            token = getattr(msg, "content", "") if msg else ""

        if not token:
            continue

        if node_name not in node_buffers:
            node_buffers[node_name] = ""
        node_buffers[node_name] += token

        yield {
            "node": node_name,
            "token": token,
            "accumulated": node_buffers[node_name],
            "is_final": False,
            "final_response": None
        }

    # Final accumulation
    yield {
        "node": "complete",
        "token": "",
        "accumulated": "",
        "is_final": True,
        "final_response": node_buffers.get("reporter", node_buffers.get("coder", ""))
    }


def stream_graph_tokens(
    graph,
    input_state: Dict[str, Any],
    config: Optional[RunnableConfig] = None
) -> Iterator[Dict[str, Any]]:
    """
    Synchronously streams LLM token chunks across LangGraph nodes using stream_mode="messages".

    Yields dictionaries:
      {
        "node": str,              # e.g. "planner", "coder", "reporter"
        "token": str,             # the current token chunk
        "accumulated": str,       # accumulated text for this node
        "is_final": bool,         # True on final completion
        "final_response": Optional[str]
      }
    """
    node_buffers: Dict[str, str] = {}

    for item in graph.stream(input_state, config=config, stream_mode="messages"):
        if isinstance(item, tuple) and len(item) == 2:
            msg, metadata = item
            node_name = metadata.get("langgraph_node", "unknown")
            token = getattr(msg, "content", "") if msg else ""
        else:
            msg = item
            node_name = "unknown"
            token = getattr(msg, "content", "") if msg else ""

        if not token:
            continue

        if node_name not in node_buffers:
            node_buffers[node_name] = ""
        node_buffers[node_name] += token

        yield {
            "node": node_name,
            "token": token,
            "accumulated": node_buffers[node_name],
            "is_final": False,
            "final_response": None
        }

    # Final completion event
    yield {
        "node": "complete",
        "token": "",
        "accumulated": "",
        "is_final": True,
        "final_response": node_buffers.get("reporter", node_buffers.get("coder", ""))
    }
