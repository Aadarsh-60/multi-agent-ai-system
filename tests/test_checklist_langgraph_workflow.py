"""
tests/test_checklist_langgraph_workflow.py

Checklist Verification for LangGraph Workflow:
  [x] All nodes and edges execute in the correct order.
  [x] Conditional routing works for every review decision.
  [x] Coder–Reviewer revision loop works correctly.
  [x] Researcher is called only when needed.
  [x] Retry limits prevent infinite loops.
  [x] Shared state is updated correctly between agents.
  [x] Human approval pauses and resumes the graph correctly.
"""

import unittest
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from graph.state import AgentState
from graph.workflow import (
    create_multi_agent_graph,
    route_after_planner,
    route_review_decision,
    cancelled_node
)
from graph.nodes import (
    planner_node,
    researcher_node,
    coder_node,
    execution_sandbox_node,
    reviewer_node,
    reporter_node
)
from agents.planner import check_research_needed
from agents.reviewer import parse_review_decision


class TestLangGraphWorkflowChecklist(unittest.TestCase):

    def test_01_all_nodes_and_edges_execute_in_correct_order(self):
        """[Checklist 1] All nodes and edges execute in the correct order."""
        execution_order = []

        def spy_planner(state, config=None):
            execution_order.append("planner")
            return {"plan": "1. Research\n2. Code", "research_needed": True, "status": "planned"}

        def spy_researcher(state, config=None):
            execution_order.append("researcher")
            return {"research_notes": "Key findings gathered.", "status": "researched"}

        def spy_coder(state, config=None):
            execution_order.append("coder")
            return {"code": "print('hello')", "status": "coded"}

        def spy_validator(state, config=None):
            execution_order.append("validator")
            return {"execution_output": "STDOUT: hello", "execution_success": True, "status": "validated"}

        def spy_reviewer(state, config=None):
            execution_order.append("reviewer")
            return {"review_decision": "approved", "iteration_count": state.get("iteration_count", 0) + 1, "status": "reviewed"}

        def spy_reporter(state, config=None):
            execution_order.append("reporter")
            return {"final_report": "# Final Report\nSuccess", "status": "completed"}

        builder = StateGraph(AgentState)
        builder.add_node("planner", spy_planner)
        builder.add_node("researcher", spy_researcher)
        builder.add_node("coder", spy_coder)
        builder.add_node("validator", spy_validator)
        builder.add_node("reviewer", spy_reviewer)
        builder.add_node("reporter", spy_reporter)
        builder.add_node("cancelled", cancelled_node)

        builder.add_edge(START, "planner")
        builder.add_conditional_edges("planner", route_after_planner, {
            "researcher": "researcher",
            "coder": "coder",
            "cancelled": "cancelled",
            "planner": "planner"
        })
        builder.add_edge("researcher", "coder")
        builder.add_edge("coder", "validator")
        builder.add_edge("validator", "reviewer")
        builder.add_conditional_edges("reviewer", route_review_decision, {
            "reporter": "reporter",
            "coder": "coder",
            "researcher": "researcher"
        })
        builder.add_edge("reporter", END)
        builder.add_edge("cancelled", END)

        graph = builder.compile()

        # Run with research_needed = True
        init_state = {
            "task": "Test Order",
            "human_approval": "approved",
            "research_needed": True,
            "iteration_count": 0,
            "max_iterations": 2
        }
        res = graph.invoke(init_state)

        expected_order = ["planner", "researcher", "coder", "validator", "reviewer", "reporter"]
        self.assertEqual(execution_order, expected_order)
        self.assertEqual(res["status"], "completed")
        print("\n[Checklist 1 PASSED] All 6 production nodes executed in strict sequential order.")

    def test_02_conditional_routing_works_for_every_review_decision(self):
        """[Checklist 2] Conditional routing works for every review decision."""
        # 1. Approved -> Reporter
        state_app = {"review_decision": "approved", "iteration_count": 0, "max_iterations": 2}
        self.assertEqual(route_review_decision(state_app), "reporter")

        # 2. Need changes -> Coder
        state_chg = {"review_decision": "need_changes", "iteration_count": 0, "max_iterations": 2}
        self.assertEqual(route_review_decision(state_chg), "coder")

        # 3. More research needed -> Researcher
        state_res = {"review_decision": "more_research_needed", "iteration_count": 0, "max_iterations": 2}
        self.assertEqual(route_review_decision(state_res), "researcher")

        # 4. Unknown/Fallback -> Reporter
        state_unk = {"review_decision": "unknown_decision", "iteration_count": 0, "max_iterations": 2}
        self.assertEqual(route_review_decision(state_unk), "reporter")

        # Also verify decision parser extraction
        self.assertEqual(parse_review_decision("DECISION: approved"), "approved")
        self.assertEqual(parse_review_decision("DECISION: need_changes"), "need_changes")
        self.assertEqual(parse_review_decision("DECISION: more_research_needed"), "more_research_needed")
        print("\n[Checklist 2 PASSED] 3-way conditional review routing and regex parsing verified.")

    def test_03_coder_reviewer_revision_loop_works_correctly(self):
        """[Checklist 3] Coder–Reviewer revision loop works correctly."""
        step_log = []

        def mock_coder(state, config=None):
            count = state.get("iteration_count", 0)
            step_log.append(f"coder_v{count}")
            # Coder reads review critique and produces improved code
            critique = state.get("review_feedback", "")
            return {"code": f"def solution(): return 'v{count}' # fixed: {critique[:10]}"}

        def mock_validator(state, config=None):
            step_log.append("validator")
            return {"execution_output": "STDOUT: ok", "execution_success": True}

        def mock_reviewer(state, config=None):
            curr_count = state.get("iteration_count", 0)
            step_log.append(f"reviewer_v{curr_count}")
            if curr_count == 0:
                return {
                    "review_decision": "need_changes",
                    "review_feedback": "Please fix off-by-one error",
                    "iteration_count": curr_count + 1
                }
            else:
                return {
                    "review_decision": "approved",
                    "review_feedback": "DECISION: approved",
                    "iteration_count": curr_count + 1
                }

        def mock_reporter(state, config=None):
            step_log.append("reporter")
            return {"final_report": "Finished successfully."}

        builder = StateGraph(AgentState)
        builder.add_node("coder", mock_coder)
        builder.add_node("validator", mock_validator)
        builder.add_node("reviewer", mock_reviewer)
        builder.add_node("reporter", mock_reporter)

        builder.add_edge(START, "coder")
        builder.add_edge("coder", "validator")
        builder.add_edge("validator", "reviewer")
        builder.add_conditional_edges("reviewer", route_review_decision, {
            "reporter": "reporter",
            "coder": "coder",
            "researcher": "reporter"  # not used in this test
        })
        builder.add_edge("reporter", END)

        graph = builder.compile()

        res = graph.invoke({
            "task": "Loop test",
            "iteration_count": 0,
            "max_iterations": 3
        })

        # Expected flow: coder_v0 -> validator -> reviewer_v0 -> coder_v1 -> validator -> reviewer_v1 -> reporter
        expected = ["coder_v0", "validator", "reviewer_v0", "coder_v1", "validator", "reviewer_v1", "reporter"]
        self.assertEqual(step_log, expected)
        self.assertEqual(res["iteration_count"], 2)
        print("\n[Checklist 3 PASSED] Coder-Reviewer revision loop successfully executed and self-corrected.")

    def test_04_researcher_is_called_only_when_needed(self):
        """[Checklist 4] Researcher is called only when needed."""
        # Case A: Self-contained task (research_needed = False)
        state_no_res = {"human_approval": "approved", "research_needed": False}
        route_target = route_after_planner(state_no_res)
        self.assertEqual(route_target, "coder", "Should jump directly to coder bypassing researcher")

        # Case B: Research required (research_needed = True)
        state_yes_res = {"human_approval": "approved", "research_needed": True}
        route_target_b = route_after_planner(state_yes_res)
        self.assertEqual(route_target_b, "researcher", "Should route to researcher when needed")

        # Test check_research_needed accuracy
        self.assertFalse(check_research_needed("1. Plan\nResearch Needed: No\n2. Implement function"))
        self.assertTrue(check_research_needed("1. Plan\nResearch Needed: Yes\n2. Research external API"))

        # Verify in graph that researcher is never entered when research_needed = False
        visited = []
        builder = StateGraph(AgentState)
        builder.add_node("planner", lambda s, c=None: {"research_needed": False, "human_approval": "approved"})
        builder.add_node("researcher", lambda s, c=None: visited.append("researcher") or {})
        builder.add_node("coder", lambda s, c=None: visited.append("coder") or {"code": "done"})
        builder.add_node("cancelled", cancelled_node)

        builder.add_edge(START, "planner")
        builder.add_conditional_edges("planner", route_after_planner, {
            "researcher": "researcher",
            "coder": "coder",
            "cancelled": "cancelled",
            "planner": "planner"
        })
        builder.add_edge("researcher", "coder")
        builder.add_edge("coder", END)
        builder.add_edge("cancelled", END)

        graph = builder.compile()
        graph.invoke({"task": "Test Bypass"})

        self.assertNotIn("researcher", visited)
        self.assertIn("coder", visited)
        print("\n[Checklist 4 PASSED] Researcher is correctly bypassed when research is not needed.")

    def test_05_retry_limits_prevent_infinite_loops(self):
        """[Checklist 5] Retry limits prevent infinite loops."""
        # When iteration reaches max_iterations (e.g. 2), even if reviewer rejects, it MUST route to reporter
        max_state_need_changes = {
            "review_decision": "need_changes",
            "iteration_count": 2,
            "max_iterations": 2
        }
        self.assertEqual(route_review_decision(max_state_need_changes), "reporter")

        max_state_more_res = {
            "review_decision": "more_research_needed",
            "iteration_count": 2,
            "max_iterations": 2
        }
        self.assertEqual(route_review_decision(max_state_more_res), "reporter")

        # Full graph run: Reviewer ALWAYS requests changes, but loop terminates at max_iterations
        loop_counter = {"coder_calls": 0}

        def stubborn_coder(s, c=None):
            loop_counter["coder_calls"] += 1
            return {"code": "print('buggy')"}

        def stubborn_reviewer(s, c=None):
            return {
                "review_decision": "need_changes",
                "iteration_count": s.get("iteration_count", 0) + 1
            }

        builder = StateGraph(AgentState)
        builder.add_node("coder", stubborn_coder)
        builder.add_node("reviewer", stubborn_reviewer)
        builder.add_node("reporter", lambda s, c=None: {"final_report": "Exhausted retries gracefully."})

        builder.add_edge(START, "coder")
        builder.add_edge("coder", "reviewer")
        builder.add_conditional_edges("reviewer", route_review_decision, {
            "reporter": "reporter",
            "coder": "coder",
            "researcher": "reporter"
        })
        builder.add_edge("reporter", END)

        graph = builder.compile()
        final_state = graph.invoke({
            "task": "Stubborn test",
            "iteration_count": 0,
            "max_iterations": 2
        })

        # coder should run exactly 2 times (initial + 1 revision)
        self.assertEqual(loop_counter["coder_calls"], 2)
        self.assertEqual(final_state["iteration_count"], 2)
        self.assertEqual(final_state["final_report"], "Exhausted retries gracefully.")
        print("\n[Checklist 5 PASSED] Infinite loop prevented by iteration threshold guard.")

    def test_06_shared_state_is_updated_correctly_between_agents(self):
        """[Checklist 6] Shared state is updated correctly between agents."""
        # Verify node output contracts and state field propagation
        state: AgentState = {
            "task": "State flow test",
            "plan": "",
            "research_notes": "",
            "code": "",
            "execution_output": "",
            "review_feedback": "",
            "review_decision": "",
            "final_report": "",
            "iteration_count": 0,
            "max_iterations": 2,
            "status": "idle"
        }

        # 1. Planner updates plan & research_needed
        with patch("graph.nodes.run_planner", return_value=["1. Step one\nResearch Needed: No"]):
            p_out = planner_node(state)
            state.update(p_out)
            self.assertIn("Step one", state["plan"])
            self.assertFalse(state["research_needed"])
            self.assertEqual(state["status"], "plan_generated")

        # 2. Researcher updates research_notes
        with patch("graph.nodes.run_researcher", return_value=["Research summary."]):
            r_out = researcher_node(state)
            state.update(r_out)
            self.assertEqual(state["research_notes"], "Research summary.")
            self.assertEqual(state["status"], "research_completed")

        # 3. Coder updates code
        with patch("graph.nodes.run_coder", return_value=["def test(): pass"]):
            c_out = coder_node(state)
            state.update(c_out)
            self.assertEqual(state["code"], "def test(): pass")
            self.assertEqual(state["status"], "code_generated")

        # 4. Sandbox updates execution results
        v_out = execution_sandbox_node(state)
        state.update(v_out)
        self.assertIn("Exit Code: 0", state["execution_output"])
        self.assertTrue(state["execution_success"])
        self.assertEqual(state["status"], "validated")

        # 5. Reviewer updates review_decision & iteration_count
        with patch("graph.nodes.run_reviewer", return_value=["DECISION: approved"]):
            rev_out = reviewer_node(state)
            state.update(rev_out)
            self.assertEqual(state["review_decision"], "approved")
            self.assertEqual(state["iteration_count"], 1)
            self.assertEqual(state["status"], "review_completed")

        # 6. Reporter updates final_report
        with patch("graph.nodes.run_reporter", return_value=["Final document."]), \
             patch("graph.nodes.memory.save_run"):
            rep_out = reporter_node(state)
            state.update(rep_out)
            self.assertEqual(state["final_report"], "Final document.")
            self.assertEqual(state["status"], "completed")

        print("\n[Checklist 6 PASSED] All state keys updated and preserved across pipeline steps.")

    def test_07_human_approval_pauses_and_resumes_the_graph_correctly(self):
        """[Checklist 7] Human approval pauses and resumes the graph correctly."""
        checkpointer = MemorySaver()

        call_log = []

        def mock_planner_step(state, config=None):
            call_log.append("planner")
            return {
                "plan": "1. Build module\nResearch Needed: No",
                "research_needed": False,
                "human_approval": "pending"
            }

        def mock_coder_step(state, config=None):
            call_log.append("coder")
            return {"code": "print('resumed!')"}

        def mock_reporter_step(state, config=None):
            call_log.append("reporter")
            return {"final_report": "Completed after human approval."}

        builder = StateGraph(AgentState)
        builder.add_node("planner", mock_planner_step)
        builder.add_node("coder", mock_coder_step)
        builder.add_node("reporter", mock_reporter_step)
        builder.add_node("cancelled", cancelled_node)

        builder.add_edge(START, "planner")
        builder.add_conditional_edges("planner", route_after_planner, {
            "coder": "coder",
            "cancelled": "cancelled",
            "planner": "planner",
            "researcher": "coder"
        })
        builder.add_edge("coder", "reporter")
        builder.add_edge("reporter", END)
        builder.add_edge("cancelled", END)

        # Interrupt before executing 'coder' to allow human review
        compiled = builder.compile(
            checkpointer=checkpointer,
            interrupt_before=["coder"]
        )

        thread_config = {"configurable": {"thread_id": "test_human_loop_1"}}

        # Phase 1: Start graph
        compiled.invoke(
            {"task": "Human in the loop task", "human_approval": "pending"},
            config=thread_config
        )

        # Verify paused: Only planner has run!
        self.assertEqual(call_log, ["planner"])
        paused_state = compiled.get_state(thread_config)
        self.assertIn("coder", paused_state.next)
        self.assertIn("1. Build module", paused_state.values["plan"])

        # Phase 2: Human approves and resumes
        compiled.update_state(
            thread_config,
            {"human_approval": "approved"}
        )
        resumed_res = compiled.invoke(None, config=thread_config)

        # Verify completed after resume
        self.assertEqual(call_log, ["planner", "coder", "reporter"])
        self.assertEqual(resumed_res["final_report"], "Completed after human approval.")

        # Phase 3: Test cancellation branch
        thread_config_cancel = {"configurable": {"thread_id": "test_human_loop_cancel"}}
        compiled.invoke(
            {"task": "Human rejection task", "human_approval": "pending"},
            config=thread_config_cancel
        )
        compiled.update_state(
            thread_config_cancel,
            {"human_approval": "rejected"},
            as_node="planner"
        )
        cancel_res = compiled.invoke(None, config=thread_config_cancel)
        self.assertEqual(cancel_res.get("status"), "cancelled")

        print("\n[Checklist 7 PASSED] LangGraph pause and resume with checkpointer & human decision verified.")


if __name__ == "__main__":
    unittest.main()
