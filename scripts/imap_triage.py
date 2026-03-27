#!/usr/bin/env python3
"""
Smart Email Triage for al.mitchell@autostarusa.com
Processes IMAP inbox and creates Todoist tasks based on email categories.
"""

import imaplib
import email
import ssl
import json
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import urllib.request
import urllib.error
import os

# Config
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
EMAIL_USER = "al.mitchell@autostarusa.com"
EMAIL_PASS = "twrp stsx tplg yvfe"

TODOIST_API_TOKEN = "67179992230c37477e22c7e230cad7d35ee10cc2"
TODOIST_WORK_PROJECT = "6gFqh9XqF8X8rff7"

STATE_FILE = "/Users/al/.openclaw/workspace/memory/gmail-state.json"

# Category keywords
NEWSLETTER_KEYWORDS = ["unsubscribe", "newsletter", "promotions", "marketing", "weekly digest", "monthly update", "noreply"]
SECURITY_KEYWORDS = ["login", "security alert", "new device", "password changed", "sign in", "verification"]
ACTION_KEYWORDS = ["need", "please", "action required", "approval", "request", "pending"]
URGENT_KEYWORDS = ["outage", "down", "critical", "escalation", "complaint", "urgent", "ASAP"]
SKIP_DOMAIN = "autostarusa.com"

def load_state():
    """Load previous state or create new."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                # Migrate old format
                if "processed" not in state:
                    state["processed"] = []
                if "stats" not in state:
                    state["stats"] = {"total": 0, "tasksCreated": 0}
                if "lastCheck" not in state and "last_check" in state:
                    state["lastCheck"] = state["last_check"]
                return state
        except:
            pass
    return {"lastCheck": None, "processed": [], "stats": {"total": 0, "tasksCreated": 0}}

def save_state(state):
    """Save state to file."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def todoist_create_task(content, priority=1, due="today"):
    """Create a Todoist task. Priority: 1=normal, 2=medium, 3=high, 4=urgent"""
    url = "https://api.todoist.com/api/v1/tasks"
    data = json.dumps({
        "content": content,
        "project_id": TODOIST_WORK_PROJECT,
        "priority": priority,
        "due_string": due
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {TODOIST_API_TOKEN}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"Todoist API error: {e.read().decode()}")
        return None
    except Exception as e:
        print(f"Todoist error: {e}")
        return None

def categorize_email(subject, sender, body):
    """Categorize email based on content."""
    text = f"{subject} {sender} {body}".lower()
    
    # Check sender domain
    is_internal = SKIP_DOMAIN in sender.lower()
    
    # Skip internal unless urgent
    if is_internal:
        if any(k in text for k in URGENT_KEYWORDS):
            return "CUSTOMER/CRITICAL"
        return "SKIP"
    
    # Check categories
    if any(k in text for k in NEWSLETTER_KEYWORDS):
        return "NEWSLETTER"
    
    if any(k in text for k in SECURITY_KEYWORDS):
        return "SECURITY"
    
    has_action = any(k in text for k in ACTION_KEYWORDS)
    has_urgent = any(k in text for k in URGENT_KEYWORDS)
    has_dealer = "dealer" in text
    
    if has_urgent or has_dealer:
        return "CUSTOMER/CRITICAL"
    
    if has_action:
        return "APPROVAL"
    
    return "GENERAL"

def process_emails():
    """Main processing function."""
    state = load_state()
    
    # Ensure stats exists
    if "stats" not in state:
        state["stats"] = {"total": 0, "tasksCreated": 0}
    
    results = {
        "processed": 0,
        "skipped": 0,
        "newsletters": 0,
        "security": 0,
        "approvals": 0,
        "critical": 0,
        "general": 0,
        "tasksCreated": 0,
        "errors": []
    }
    
    task_list = []
    critical_alerts = []
    
    try:
        # Connect to IMAP
        context = ssl.create_default_context()
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT, ssl_context=context)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("INBOX")
        
        # Search for unread emails
        status, messages = mail.search(None, "UNSEEN")
        
        if status != "OK" or not messages[0]:
            print("No new unread emails.")
            mail.logout()
            save_state(state)
            return results, task_list, critical_alerts
        
        msg_ids = messages[0].split()
        print(f"Found {len(msg_ids)} unread emails")
        
        # Calculate cutoff time (1 hour ago)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
        
        for msg_id in msg_ids:
            try:
                status, msg_data = mail.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue
                
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Extract fields
                subject = msg.get("Subject", "")
                sender = msg.get("From", "")
                date_str = msg.get("Date", "")
                
                # Parse date
                try:
                    email_date = parsedate_to_datetime(date_str)
                    if email_date.tzinfo is None:
                        email_date = email_date.replace(tzinfo=timezone.utc)
                except:
                    email_date = datetime.now(timezone.utc)
                
                # Skip if older than 1 hour
                if email_date < cutoff_time:
                    results["skipped"] += 1
                    continue
                
                # Extract body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            try:
                                body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                break
                            except:
                                pass
                else:
                    try:
                        body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        pass
                
                # Categorize
                category = categorize_email(subject, sender, body)
                
                # Clean sender name
                sender_clean = re.sub(r'<.*?>', '', sender).strip()
                if not sender_clean:
                    sender_clean = sender
                
                results["processed"] += 1
                
                if category == "SKIP":
                    results["skipped"] += 1
                    # Mark as read - internal non-urgent
                    mail.store(msg_id, '+FLAGS', '\\Seen')
                    continue
                
                if category == "NEWSLETTER":
                    results["newsletters"] += 1
                    # Mark as read, no task
                    mail.store(msg_id, '+FLAGS', '\\Seen')
                    continue
                
                if category == "SECURITY":
                    results["security"] += 1
                    # Flag but don't task, mark read
                    mail.store(msg_id, '+FLAGS', '\\Seen')
                    continue
                
                # Create task for actionable emails
                task_content = f"📧 {subject[:60]}... from {sender_clean[:30]}" if len(subject) > 60 else f"📧 {subject} from {sender_clean[:30]}"
                
                if category == "CUSTOMER/CRITICAL":
                    results["critical"] += 1
                    todoist_create_task(task_content, priority=4)
                    results["tasksCreated"] += 1
                    task_list.append(f"🔴 CRITICAL: {subject[:50]}... ({sender_clean[:25]})")
                    critical_alerts.append({"subject": subject, "sender": sender_clean, "category": category})
                
                elif category == "APPROVAL":
                    results["approvals"] += 1
                    todoist_create_task(task_content, priority=2)
                    results["tasksCreated"] += 1
                    task_list.append(f"🟡 APPROVAL: {subject[:50]}... ({sender_clean[:25]})")
                
                elif category == "GENERAL":
                    results["general"] += 1
                    todoist_create_task(task_content, priority=1)
                    results["tasksCreated"] += 1
                    task_list.append(f"🔵 GENERAL: {subject[:50]}... ({sender_clean[:25]})")
                
                # Mark as read
                mail.store(msg_id, '+FLAGS', '\\Seen')
                
                # Track in state
                state["processed"].append({
                    "id": msg_id.decode(),
                    "subject": subject,
                    "sender": sender,
                    "category": category,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
            except Exception as e:
                results["errors"].append(f"Error processing msg {msg_id}: {str(e)}")
                continue
        
        mail.logout()
        
    except Exception as e:
        results["errors"].append(f"IMAP error: {str(e)}")
    
    # Update state
    state["lastCheck"] = datetime.now(timezone.utc).isoformat()
    state["stats"]["total"] += results["processed"]
    state["stats"]["tasksCreated"] += results["tasksCreated"]
    
    # Keep only last 100 processed
    if len(state["processed"]) > 100:
        state["processed"] = state["processed"][-100:]
    
    save_state(state)
    
    return results, task_list, critical_alerts

if __name__ == "__main__":
    results, tasks, critical = process_emails()
    
    # Output JSON for summary
    output = {
        "results": results,
        "tasks": tasks,
        "critical": critical,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    print(json.dumps(output, indent=2))
