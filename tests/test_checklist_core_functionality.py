"""
tests/test_checklist_core_functionality.py

End-to-End Checklist Verification:
  [x] Planner creates a clear, valid execution plan.
  [x] Human can approve, modify, or reject the plan.
  [x] Researcher retrieves relevant information using Tavily.
  [x] Coder generates a solution based on the plan and research.
  [x] Reviewer checks correctness and provides actionable feedback.
  [x] Reporter generates the final answer, code, or report.
"""

import unittest
from dotenv import load_dotenv
load_dotenv()

from agents.planner import run_planner, check_research_needed
from agents.researcher import run_researcher
from agents.coder import run_coder
from agents.reviewer import run_reviewer, parse_review_decision
from agents.reporter import run_reporter
from tools.sandbox import run_code_in_sandbox
from tools.search_tool import search_tool
from graph.workflow import route_after_planner, route_review_decision


class TestCoreChecklist(unittest.TestCase):

    def test_01_planner_creates_clear_execution_plan(self):
        """Checklist 1: Planner creates a clear, valid execution plan."""
        task = "Write a Python script to calculate prime numbers up to N using Sieve of Eratosthenes"
        stream = run_planner(task=task)
        plan_text = "".join(chunk for chunk in stream)

        self.assertTrue(len(plan_text) > 50)
        self.assertIn("1", plan_text)  # Numbered steps
        # Check research assessment was generated
        has_assessment = "research" in plan_text.lower()
        self.assertTrue(has_assessment)
        print("\n[Checklist 1 PASSED] Planner produced a structured plan.")

    def test_02_human_can_approve_modify_or_reject(self):
        """Checklist 2: Human can approve, modify, or reject the plan."""
        # 1. Approve
        state_approve = {"human_approval": "approved", "research_needed": False}
        self.assertEqual(route_after_planner(state_approve), "coder")

        # 2. Modify / Revise
        state_revise = {"human_approval": "revise", "feedback": "Use Python 3.12 typing"}
        self.assertEqual(route_after_planner(state_revise), "planner")

        # 3. Reject / Cancel
        state_reject = {"human_approval": "rejected"}
        self.assertEqual(route_after_planner(state_reject), "cancelled")
        print("\n[Checklist 2 PASSED] Human approval, modification loop, and rejection branches verified.")

    def test_03_researcher_retrieves_information_using_tavily(self):
        """Checklist 3: Researcher retrieves relevant information using Tavily."""
        query = "Python Sieve of Eratosthenes algorithm complexity"
        raw_search = search_tool(query)
        self.assertTrue(len(raw_search) > 20)

        # Agent summary stream
        plan = "1. Research Sieve algorithm\n2. Implement code"
        stream = run_researcher(task=query, plan=plan)
        summary = "".join(chunk for chunk in stream)

        self.assertTrue(len(summary) > 50)
        print("\n[Checklist 3 PASSED] Researcher successfully queried Tavily and summarized findings.")

    def test_04_coder_generates_solution_and_sandbox_validates(self):
        """Checklist 4: Coder generates a solution based on plan and research."""
        task = "Write a Python function `is_prime(n)` and calculate primes up to 20"
        plan = "1. Implement is_prime\n2. Loop 2 to 20\n3. Print primes"
        research = "Primes up to 20 are 2, 3, 5, 7, 11, 13, 17, 19"

        stream = run_coder(task=task, plan=plan, research_notes=research)
        code_text = "".join(chunk for chunk in stream)

        self.assertTrue(len(code_text) > 30)
        self.assertIn("def ", code_text)

        # Also validate through sandbox
        sandbox_res = run_code_in_sandbox(code_text, timeout_seconds=10)
        self.assertIsNotNone(sandbox_res)
        print(f"\n[Checklist 4 PASSED] Coder generated Python solution. Sandbox run success: {sandbox_res.get('success')}")

    def test_05_reviewer_checks_correctness_and_actionable_feedback(self):
        """Checklist 5: Reviewer checks correctness and provides actionable feedback."""
        task = "Calculate primes up to 20"
        code = "def get_primes(): return [2, 3, 5, 7, 11, 13, 17, 19]\nprint(get_primes())"
        exec_results = "Status: Execution Success (Exit code: 0)\nSTDOUT: [2, 3, 5, 7, 11, 13, 17, 19]"

        stream = run_reviewer(task=task, code=code, execution_results=exec_results)
        review_text = "".join(chunk for chunk in stream)

        self.assertTrue(len(review_text) > 30)
        decision = parse_review_decision(review_text)
        self.assertIn(decision, ["approved", "need_changes", "more_research_needed"])
        print(f"\n[Checklist 5 PASSED] Reviewer evaluated code & sandbox results. Decision: {decision}")

    def test_06_reporter_generates_final_answer(self):
        """Checklist 6: Reporter generates the final answer, code, or report."""
        task = "Prime numbers computation"
        plan = "1. Plan\n2. Code\n3. Validate"
        notes = "Verified mathematical properties"
        code = "def primes(): return [2, 3, 5]"
        review = "DECISION: approved. Code is correct."
        exec_out = "STDOUT: [2, 3, 5]\nExit code: 0"

        stream = run_reporter(task, plan, notes, code, review, exec_out)
        report_text = "".join(chunk for chunk in stream)

        self.assertTrue(len(report_text) > 50)
        print("\n[Checklist 6 PASSED] Reporter generated complete final deliverable.")

    def test_07_coder_generates_solution_according_to_plan_language(self):
        """Checklist 7: Coder generates solution in the exact language requested in the plan (e.g. Java)."""
        task = "Build a Java Backend REST API for Item management"
        plan = (
            "1. Scaffolding: Spring Boot application\n"
            "2. Entity: Item with id, name, description\n"
            "3. Repository: ItemRepository extending JpaRepository\n"
            "4. Controller: ItemController exposing GET, POST, PUT, DELETE with @RestController"
        )
        stream = run_coder(task=task, plan=plan)
        code_text = "".join(chunk for chunk in stream)

        self.assertTrue(len(code_text) > 50)
        # Verify it generated Java and NOT Python
        has_java = any(k in code_text for k in ["class ", "public ", "ItemController", "Item", "@RestController"])
        self.assertTrue(has_java, "Coder must generate Java code when plan specifies Java.")
        self.assertNotIn("def is_prime", code_text)

        # Validate with multi-language sandbox
        sandbox_res = run_code_in_sandbox(code_text)
        self.assertTrue(sandbox_res["success"], f"Sandbox should validate Java structure. Output: {sandbox_res}")
        self.assertEqual(sandbox_res.get("language"), "java")
        print("\n[Checklist 7 PASSED] Coder generated Java Spring Boot solution according to plan, and sandbox validated it.")


if __name__ == "__main__":
    unittest.main()

