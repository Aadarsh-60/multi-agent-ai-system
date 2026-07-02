"""
tools/notifier.py

Provides notifications (Slack, Email) when a workflow run completes.
"""

import os
import requests

def send_slack_notification(message: str):
    """Sends a message to Slack using a webhook URL."""
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    
    if not webhook_url:
        print(f"[Slack Notification] Webhook URL not set. Mock message: {message}")
        return
        
    try:
        response = requests.post(
            webhook_url,
            json={"text": message}
        )
        response.raise_for_status()
        print("[Slack Notification] Successfully sent message.")
    except Exception as e:
        print(f"[Slack Notification] Failed to send message: {e}")


def send_email_notification(subject: str, body: str):
    """Sends an email notification."""
    # In a real app, you would use smtplib or a service like SendGrid/Mailgun.
    # We will just print to console for demonstration if no provider is configured.
    print(f"\n[Email Notification]\nSubject: {subject}\nBody:\n{body}\n")


def notify_run_finished(task: str, report_preview: str):
    """Convenience method to fire all notifications."""
    message = f"✅ *Multi-Agent Run Completed*\n*Task:* {task}\n*Preview:* {report_preview[:100]}..."
    send_slack_notification(message)
    send_email_notification("Multi-Agent Run Completed", f"Task: {task}\n\n{report_preview[:500]}...")
