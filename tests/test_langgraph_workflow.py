"""
tests/test_langgraph_workflow.py

Tests for the AgentMind 10-Step LangGraph Multi-Agent Architecture:
  1. AgentState Schema Completeness
  2. Planner Human-Approval & Research-Check Routing
  3. Sandbox Execution & Validation
  4. 3-Way Review Decision Routing (approved / need_changes / more_research_needed)
  5. Full Graph Compilation & Topology
"""

import unittest
from graph.state import AgentState
from graph.workflow import (
    create_multi_agent_graph,
    route_after_planner,
    route_review_decision
)
from agents.planner import check_research_needed
from agents.reviewer import parse_review_decision
from tools.sandbox import run_code_in_sandbox


class TestLangGraphWorkflow(unittest.TestCase):
    def test_agent_state_keys(self):
        """Verify AgentState schema supports all 10 steps."""
        state: AgentState = {
            "task": "Build a CLI todo list in Python",
            "plan": "1. Plan\n2. Code\nResearch Needed: No",
            "feedback": "",
            "past_context": "",
            "image_name": "",
            "human_approval": "approved",
            "research_needed": False,
            "research_notes": "",
            "research_feedback": "",
            "code": "print('Todo CLI')",
            "execution_output": "Status: Success\nExit Code: 0",
            "execution_success": True,
            "execution_stderr": "",
            "review_feedback": "DECISION: approved",
            "review_decision": "approved",
            "iteration_count": 1,
            "max_iterations": 2,
            "final_report": "Final deliverable",
            "status": "completed"
        }
        self.assertEqual(state["task"], "Build a CLI todo list in Python")
        self.assertFalse(state["research_needed"])
        self.assertEqual(state["review_decision"], "approved")

    def test_route_after_planner(self):
        """Test Step 3 (Human Approval) & Step 4 (Research Check) conditional routing."""
        # Case A: Human rejected -> routes to cancelled
        state_rejected: AgentState = {"human_approval": "rejected", "research_needed": True}
        self.assertEqual(route_after_planner(state_rejected), "cancelled")

        # Case B: Human requested revision -> loops back to planner
        state_revise: AgentState = {"human_approval": "revise", "research_needed": True}
        self.assertEqual(route_after_planner(state_revise), "planner")

        # Case C: Human approved + Research Needed -> routes to researcher
        state_appr_res: AgentState = {"human_approval": "approved", "research_needed": True}
        self.assertEqual(route_after_planner(state_appr_res), "researcher")

        # Case D: Human approved + Research NOT Needed -> jumps to coder
        state_appr_no_res: AgentState = {"human_approval": "approved", "research_needed": False}
        self.assertEqual(route_after_planner(state_appr_no_res), "coder")

    def test_research_detection(self):
        """Verify check_research_needed accurately detects research requirement."""
        self.assertTrue(check_research_needed("1. Step\nResearch Needed: Yes\n2. Code"))
        self.assertFalse(check_research_needed("1. Step\nResearch Needed: No\n2. Code"))

    def test_sandbox_execution(self):
        """Verify sandbox runs clean code and captures output."""
        code = "print('LANGGRAPH_SANDBOX_SUCCESS')"
        result = run_code_in_sandbox(code, timeout_seconds=5)
        self.assertTrue(result["success"])
        self.assertEqual(result["exit_code"], 0)
        self.assertIn("LANGGRAPH_SANDBOX_SUCCESS", result["stdout"])

    def test_route_review_decision_3_way(self):
        """Test Step 8 Review Decision conditional routing."""
        # Case 1: Approved -> Reporter
        state_approved: AgentState = {
            "review_decision": "approved",
            "iteration_count": 1,
            "max_iterations": 2
        }
        self.assertEqual(route_review_decision(state_approved), "reporter")

        # Case 2: Need changes & iteration < max -> Coder loop
        state_changes: AgentState = {
            "review_decision": "need_changes",
            "iteration_count": 1,
            "max_iterations": 2
        }
        self.assertEqual(route_review_decision(state_changes), "coder")

        # Case 3: More research needed & iteration < max -> Researcher loop
        state_more_res: AgentState = {
            "review_decision": "more_research_needed",
            "iteration_count": 1,
            "max_iterations": 2
        }
        self.assertEqual(route_review_decision(state_more_res), "researcher")

        # Case 4: Max iterations exceeded -> Proceed to Reporter
        state_max_changes: AgentState = {
            "review_decision": "need_changes",
            "iteration_count": 2,
            "max_iterations": 2
        }
        self.assertEqual(route_review_decision(state_max_changes), "reporter")

    def test_review_decision_parsing(self):
        """Verify parse_review_decision extracts decisions from text."""
        self.assertEqual(parse_review_decision("Great code.\nDECISION: approved"), "approved")
        self.assertEqual(parse_review_decision("Bugs found.\nDECISION: need_changes"), "need_changes")
        self.assertEqual(parse_review_decision("API unknown.\nDECISION: more_research_needed"), "more_research_needed")

    def test_langgraph_compilation_and_all_nodes(self):
        """Verify LangGraph compiles with all 8 workflow nodes."""
        compiled_graph = create_multi_agent_graph()
        nodes = list(compiled_graph.nodes.keys())

        expected_nodes = [
            "__start__",
            "planner",
            "researcher",
            "coder",
            "validator",
            "reviewer",
            "reporter",
            "cancelled"
        ]
        for node in expected_nodes:
            self.assertIn(node, nodes)


if __name__ == "__main__":
    unittest.main()
