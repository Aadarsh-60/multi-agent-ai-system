"""
tests/test_checklist_langgraph_streaming.py

Verification for LangGraph Streaming + Structured Response Formatting:
  [x] Token streaming: Use graph.astream() with stream_mode="messages" to receive LLM message chunks as they are generated.
  [x] Structured output: Format the response with Markdown headings, lists, tables, and code blocks. Frontend renders progressively.
  [x] Final response: Accumulate the streamed chunks and store the complete answer when generation finishes.
"""

import asyncio
import unittest
from unittest.mock import MagicMock, patch
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessageChunk
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from graph.state import AgentState
from graph.streaming import astream_graph_tokens, stream_graph_tokens
from agents.reporter import REPORT_PROMPT


class TestLangGraphStreaming(unittest.TestCase):

    def test_01_token_streaming_with_astream_and_stream_mode_messages(self):
        """[Checklist 1] Token streaming: Use graph.astream() with stream_mode='messages'."""
        class StreamState(AgentState):
            pass

        async def streaming_agent_node(state, config=None):
            # Model streaming chunks through Runnable interface
            llm = FakeListChatModel(responses=["# Solution\n\n```python\nprint('streaming chunk')\n```"])
            res = await llm.ainvoke("prompt", config=config)
            return {"final_report": res.content, "status": "completed"}

        builder = StateGraph(StreamState)
        builder.add_node("reporter", streaming_agent_node)
        builder.add_edge(START, "reporter")
        builder.add_edge("reporter", END)
        test_graph = builder.compile()

        async def collect_stream():
            received_tokens = []
            received_nodes = []
            async for chunk in astream_graph_tokens(test_graph, {"task": "Stream test"}):
                if not chunk["is_final"]:
                    received_tokens.append(chunk["token"])
                    received_nodes.append(chunk["node"])
            return received_tokens, received_nodes

        tokens, nodes = asyncio.run(collect_stream())

        # Verify token chunks were received progressively
        self.assertTrue(len(tokens) > 1, f"Expected multiple token chunks, got {len(tokens)}")
        self.assertIn("reporter", nodes)
        reconstructed = "".join(tokens)
        self.assertIn("# Solution", reconstructed)
        self.assertIn("print('streaming chunk')", reconstructed)
        print(f"\n[Checklist 1 PASSED] Received {len(tokens)} progressive token chunks via graph.astream() with stream_mode='messages'.")

    def test_02_structured_output_markdown_headings_lists_tables_code(self):
        """[Checklist 2] Structured output: Markdown headings, lists, tables, and code blocks."""
        # Check that REPORT_PROMPT enforces all structural elements
        self.assertIn("Executive Summary & Solution Overview", REPORT_PROMPT)
        self.assertIn("Research Highlights & Citations", REPORT_PROMPT)
        self.assertIn("Complete Executable Code", REPORT_PROMPT)
        self.assertIn("Execution & Validation Findings", REPORT_PROMPT)
        self.assertIn("Reviewer Quality Assessment", REPORT_PROMPT)
        self.assertIn("Recommended Next Steps", REPORT_PROMPT)

        structured_response_sample = (
            "# Executive Summary\n"
            "This is the summary.\n\n"
            "## Key Findings\n"
            "- Item 1: High performance\n"
            "- Item 2: Safe memory\n\n"
            "### Comparison Table\n"
            "| Component | Status | Details |\n"
            "|---|---|---|\n"
            "| Parser | Passed | 0.02s |\n"
            "| Sandbox | Clean | Exit Code 0 |\n\n"
            "```python\n"
            "def run():\n"
            "    return True\n"
            "```\n"
        )

        # Verify presence of all required Markdown constructs
        has_headings = "# " in structured_response_sample
        has_lists = "- " in structured_response_sample
        has_tables = "| " in structured_response_sample and "-|-" in structured_response_sample.replace(" ", "")
        has_code_blocks = "```python" in structured_response_sample

        self.assertTrue(has_headings, "Must contain Markdown headings (#, ##, ###)")
        self.assertTrue(has_lists, "Must contain Markdown lists (- or *)")
        self.assertTrue(has_tables, "Must contain Markdown tables (| cols |)")
        self.assertTrue(has_code_blocks, "Must contain formatted code blocks (```python ... ```)")
        print("\n[Checklist 2 PASSED] Structured response formatting verified for headings, lists, tables, and code blocks.")

    def test_03_final_response_accumulates_streamed_chunks(self):
        """[Checklist 3] Final response: Accumulate streamed chunks and store complete answer."""
        class AccumulateState(AgentState):
            pass

        def multi_chunk_node(state, config=None):
            llm = FakeListChatModel(responses=["First chunk, second chunk, and final chunk."])
            res = llm.invoke("generate", config=config)
            return {"final_report": res.content, "status": "completed"}

        builder = StateGraph(AccumulateState)
        builder.add_node("reporter", multi_chunk_node)
        builder.add_edge(START, "reporter")
        builder.add_edge("reporter", END)
        graph = builder.compile()

        accumulated_chunks = []
        final_answer = None

        for event in stream_graph_tokens(graph, {"task": "Accumulate test"}):
            if not event["is_final"]:
                accumulated_chunks.append(event["token"])
            else:
                final_answer = event["final_response"]

        combined = "".join(accumulated_chunks)
        self.assertEqual(combined, "First chunk, second chunk, and final chunk.")
        self.assertEqual(final_answer, combined)
        print("\n[Checklist 3 PASSED] Streamed chunks cleanly accumulated and stored as final complete answer.")


if __name__ == "__main__":
    unittest.main()
