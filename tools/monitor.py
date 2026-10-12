"""
tools/monitor.py

Telemetry, Logging, and Observability for AgentMind Multi-Agent System:
  - Tracks token usage (input and output)
  - Measures execution latency per node and cumulative pipeline runtime
  - Estimates API cost in USD
  - Records errors with stack traces
  - Generates structured run logs and debug traces for failed/successful runs
"""

import os
import time
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configure logging
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "pipeline_trace.log")

logger = logging.getLogger("AgentMind.Telemetry")
logger.setLevel(logging.INFO)

if not logger.handlers:
    # File handler
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(file_formatter)
    logger.addHandler(console_handler)


def count_tokens(text: str) -> int:
    """Estimates or counts tokens accurately."""
    if not text:
        return 0
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        # High-accuracy fallback: ~3.8 chars per token for English & code
        return max(1, int(len(text) / 3.8))


class NodeSpan:
    """Represents a single agent node execution span."""
    def __init__(self, node_name: str):
        self.node_name = node_name
        self.start_time = time.perf_counter()
        self.end_time: Optional[float] = None
        self.latency_seconds: float = 0.0
        self.input_tokens: int = 0
        self.output_tokens: int = 0
        self.status: str = "running"
        self.error: Optional[str] = None
        self.timestamp = datetime.utcnow().isoformat()

    def complete(self, input_text: str = "", output_text: str = "", error: Optional[str] = None):
        self.end_time = time.perf_counter()
        self.latency_seconds = round(self.end_time - self.start_time, 4)
        self.input_tokens = count_tokens(input_text)
        self.output_tokens = count_tokens(output_text)
        if error:
            self.status = "failed"
            self.error = error
        else:
            self.status = "success"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_name": self.node_name,
            "timestamp": self.timestamp,
            "latency_seconds": self.latency_seconds,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.input_tokens + self.output_tokens,
            "status": self.status,
            "error": self.error
        }


class PipelineMonitor:
    """
    Central monitor tracking token usage, latency, API costs,
    and error debugging traces across all agent nodes.
    """

    # Estimated pricing per 1M tokens ($0.59 input, $0.79 output for standard open-weights models)
    PRICE_INPUT_PER_1M = 0.59
    PRICE_OUTPUT_PER_1M = 0.79

    def __init__(self):
        self.spans: List[NodeSpan] = []
        self.errors: List[Dict[str, Any]] = []
        self._active_spans: Dict[str, NodeSpan] = {}
        self.start_time = time.perf_counter()

    def start_span(self, node_name: str) -> NodeSpan:
        """Starts timing a node execution."""
        span = NodeSpan(node_name)
        self._active_spans[node_name] = span
        logger.info(f"NODE START: [{node_name}]")
        return span

    def end_span(
        self,
        node_name: str,
        input_text: str = "",
        output_text: str = "",
        error: Optional[str] = None
    ) -> Optional[NodeSpan]:
        """Ends timing and logs metrics for a node execution."""
        span = self._active_spans.pop(node_name, None)
        if not span:
            span = NodeSpan(node_name)
        span.complete(input_text=input_text, output_text=output_text, error=error)
        self.spans.append(span)

        if error:
            self.record_error(node_name, error)
            logger.error(f"NODE FAILED: [{node_name}] | Latency: {span.latency_seconds}s | Error: {error}")
        else:
            logger.info(
                f"NODE FINISHED: [{node_name}] | Latency: {span.latency_seconds}s | "
                f"Tokens: {span.input_tokens} in / {span.output_tokens} out"
            )

        return span

    def record_error(self, node_name: str, error_message: str):
        """Records an error event for debugging."""
        err_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "node_name": node_name,
            "error": str(error_message)
        }
        self.errors.append(err_entry)
        logger.error(f"DEBUG TRACE: Error in [{node_name}]: {error_message}")

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimates cost in USD based on token counts."""
        cost_in = (input_tokens / 1_000_000.0) * self.PRICE_INPUT_PER_1M
        cost_out = (output_tokens / 1_000_000.0) * self.PRICE_OUTPUT_PER_1M
        return round(cost_in + cost_out, 6)

    def get_summary(self) -> Dict[str, Any]:
        """Returns consolidated metrics across all executed spans."""
        total_input_tokens = sum(s.input_tokens for s in self.spans)
        total_output_tokens = sum(s.output_tokens for s in self.spans)
        total_tokens = total_input_tokens + total_output_tokens
        total_latency = round(sum(s.latency_seconds for s in self.spans), 3)
        total_cost = self.calculate_cost(total_input_tokens, total_output_tokens)

        node_breakdown = {s.node_name: s.to_dict() for s in self.spans}

        return {
            "total_tokens": total_tokens,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "total_latency_seconds": total_latency,
            "estimated_cost_usd": total_cost,
            "error_count": len(self.errors),
            "errors": self.errors,
            "node_breakdown": node_breakdown
        }

    def get_debug_trace(self) -> str:
        """Returns a formatted trace string useful for debugging failed runs."""
        trace_lines = ["=== AGENTMIND EXECUTION DEBUG TRACE ==="]
        for span in self.spans:
            status_icon = "❌" if span.status == "failed" else "✅"
            trace_lines.append(
                f"{status_icon} Node: {span.node_name} | Status: {span.status} | "
                f"Latency: {span.latency_seconds}s | Tokens: {span.input_tokens}+{span.output_tokens}={span.input_tokens + span.output_tokens}"
            )
            if span.error:
                trace_lines.append(f"   ↳ Error Details: {span.error}")

        if self.errors:
            trace_lines.append(f"\nTotal Errors Recorded: {len(self.errors)}")
            for idx, err in enumerate(self.errors, start=1):
                trace_lines.append(f"  {idx}. [{err['node_name']}] {err['error']}")
        else:
            trace_lines.append("\nNo uncaught errors recorded during run.")

        return "\n".join(trace_lines)

    def reset(self):
        """Clears spans and error state for a new run."""
        self.spans.clear()
        self.errors.clear()
        self._active_spans.clear()
        self.start_time = time.perf_counter()


# Global telemetry singleton
monitor = PipelineMonitor()
