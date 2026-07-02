"""
main.py

Simplest way to run the whole system from the terminal.
This is where the human-in-the-loop approval actually shows up
as a y/n prompt in your console.

Usage:
    python main.py
"""

from dotenv import load_dotenv
load_dotenv()

from workflows.graph import run_multi_agent_system

if __name__ == "__main__":
    print("=== Multi-Agent AI System ===")
    task = input("Describe your task: ")

    final_state = run_multi_agent_system(task)

    print("\n\n================ FINAL REPORT ================\n")
    print(final_state["final_report"])
