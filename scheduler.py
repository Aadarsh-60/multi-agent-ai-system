"""
scheduler.py

Runs background recurring tasks using the multi-agent graph, bypassing the human approval step.
"""

import schedule
import time
import threading
from workflows.graph import run_multi_agent_system
import workflows.human_loop

# Mock human approval to always say YES for scheduled headless runs
workflows.human_loop.ask_human_approval = lambda plan: True

def scheduled_job():
    print("\n[Scheduler] Running scheduled task...")
    task = "Find the latest news on AI agents and summarize it."
    try:
        final_state = run_multi_agent_system(task)
        print("[Scheduler] Scheduled task finished successfully.")
    except Exception as e:
        print(f"[Scheduler] Error running task: {e}")

def run_scheduler():
    """Runs the scheduler continuously."""
    # For demonstration, we'll schedule it every day at 10:00 AM, 
    # and also run it once immediately if we want (commented out).
    schedule.every().day.at("10:00").do(scheduled_job)
    
    # Or to test it quickly:
    # schedule.every(10).seconds.do(scheduled_job)

    print("[Scheduler] Started background scheduler.")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    run_scheduler()
