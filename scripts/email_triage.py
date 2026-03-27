#!/usr/bin/env python3
"""Smart email triage for al.mitchell@autostarusa.com"""

import imaplib
import ssl
import email
import email.policy
import json
import re
from datetime import datetime, timedelta, timezone
import urllib.request
import urllib.error

# Config
IMAP_SERVER = "imap.gmail.com"
IMAP_USER = "al.mitchell@autostarusa.com"
IMAP_PASS = "twrp stsx tplg yvfe"
TODOIST_TOKEN = "67179992230c37477e22c7e230cad7d35ee10cc2"
TODOIST_WORK_PROJECT = "6gFqh9XqF8X8rff7"
TELEGRAM_CHAT = "6038232911"

# Categories
NEWSLETTER_KEYWORDS = ["unsubscribe", "newsletter", "promotions", "marketing", 
                       "weekly digest", "monthly update", "noreply", "promo"]
SECURITY_KEYWORDS = ["login", "security alert", "new device", "password changed", 
                     "sign in", "security check"]
URGENT_KEYWORDS = ["urgent", "critical", "escalation", "outage", "down", "emergency"]
CUSTOMER_KEYWORDS = ["outage", "down", "critical", "escalation", "complaint", 
                     "urgent", "ASAP", "dealer"]
ACTION_KEYWORDS = ["need", "please", "action required", "approval", "request", "pending"]

def get_email_body(msg):
    """Extract plain text body from email"""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                try:
                    body = part.get_content()
                    break
                except:
                    pass
    else:
        try:
            body = msg.get_content()
        except:
            pass
    return body[:2000] if body else ""

def categorize_email(subject, sender, body):
    """Categorize email and return (category, priority, alert)"""
    text = f"{subject} {sender} {body}".lower()
    
    # Check if internal (autostarusa.com)
    is_internal = "autostarusa.com" in sender.lower()
    has_urgent = any(k in text for k in URGENT_KEYWORDS)
    
    # Skip internal unless urgent
    if is_internal and not has_urgent:
        return ("SKIP", None, False)
    
    # Newsletters - auto-mark read
    if any(k in text for k in NEWSLETTER_KEYWORDS):
        return ("NEWSLETTER", None, False)
    
    # Security alerts - flag but no task
    if any(k in text for k in SECURITY_KEYWORDS):
        return ("SECURITY", None, False)
    
    # Customer/Critical - high priority + alert
    if any(k in text for k in CUSTOMER_KEYWORDS) and not is_internal:
        return ("CUSTOMER", 4, True)  # High priority
    
    # Approvals - medium priority
    if "approval" in text or ("request" in text and "pending" in text):
        return ("APPROVAL", 3, False)  # Medium priority
    
    # General actionable
    has_action = any(k in text for k in ACTION_KEYWORDS)
    if has_action:
        return ("GENERAL", 2, False)  # Normal priority
    
    return ("SKIP", None, False)

def create_todoist_task(content, priority):
    """Create Todoist task via API"""
    url = "https://api.todoist.com/api/v1/tasks"
    headers = {
        "Authorization": f"Bearer {TODOIST_TOKEN}",
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "content": content,
        "project_id": TODOIST_WORK_PROJECT,
        "priority": priority,
        "due_string": "today"
    }).encode()
    
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"Todoist error: {e.code} {e.reason}")
        return None

def send_telegram_alert(message):
    """Send critical alert via Telegram bot"""
    # Using the message tool instead
    print(f"[ALERT] {message}")

def main():
    results = {
        "processed": 0,
        "tasks_created": 0,
        "categories": {},
        "alerts": [],
        "errors": []
    }
    
    try:
        # Connect to IMAP
        print("Connecting to IMAP...")
        context = ssl.create_default_context()
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, ssl_context=context)
        mail.login(IMAP_USER, IMAP_PASS.replace(" ", ""))
        mail.select("INBOX")
        
        # Search for unread emails from last hour
        since_time = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(UNSEEN SINCE "{since_time}")')
        
        if status != "OK":
            results["errors"].append(f"Search failed: {status}")
            print(json.dumps(results, indent=2))
            return
        
        msg_ids = messages[0].split()
        results["found"] = len(msg_ids)
        print(f"Found {len(msg_ids)} unread emails")
        
        for msg_id in msg_ids:
            try:
                status, msg_data = mail.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue
                
                msg = email.message_from_bytes(msg_data[0][1], policy=email.policy.default)
                subject = msg.get("subject", "(No Subject)")
                sender = msg.get("from", "Unknown")
                date_str = msg.get("date", "")
                body = get_email_body(msg)
                
                # Extract sender email
                sender_match = re.search(r'<([^>]+)>', sender)
                sender_email = sender_match.group(1) if sender_match else sender
                
                category, priority, alert = categorize_email(subject, sender_email, body)
                
                results["categories"][category] = results["categories"].get(category, 0) + 1
                
                if category == "SKIP":
                    # Still mark as read
                    mail.store(msg_id, "+FLAGS", "\\Seen")
                    results["skipped_details"] = results.get("skipped_details", []) + [f"{sender_email}: {subject[:50]}"]
                    results["processed"] += 1
                    continue
                
                if category == "NEWSLETTER":
                    # Auto-mark read, no task
                    mail.store(msg_id, "+FLAGS", "\\Seen")
                    results["processed"] += 1
                    continue
                
                if category == "SECURITY":
                    # Flag but don't task
                    mail.store(msg_id, "+FLAGS", "\\Flagged")
                    mail.store(msg_id, "+FLAGS", "\\Seen")
                    results["processed"] += 1
                    continue
                
                # Create Todoist task for actionable emails
                task_content = f"📧 {subject[:60]}... from {sender_email[:40]}"
                task = create_todoist_task(task_content, priority)
                
                if task:
                    results["tasks_created"] += 1
                    
                    if alert:
                        alert_msg = f"🚨 {category}: {subject[:50]} from {sender_email}"
                        results["alerts"].append(alert_msg)
                
                # Mark as read
                mail.store(msg_id, "+FLAGS", "\\Seen")
                results["processed"] += 1
                
            except Exception as e:
                results["errors"].append(f"Error processing {msg_id}: {str(e)}")
                continue
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        results["errors"].append(f"IMAP error: {str(e)}")
    
    # Save state
    with open("/Users/al/.openclaw/workspace/gmail-state.json", "w") as f:
        json.dump({
            "last_run": datetime.now(timezone.utc).isoformat(),
            "results": results
        }, f, indent=2)
    
    # Print summary
    summary = f"""📧 Email Triage Complete

Found: {results.get('found', 0)} unread emails
Processed: {results['processed']}
Tasks created: {results['tasks_created']}

Categories:
{chr(10).join(f"  • {k}: {v}" for k, v in results['categories'].items())}
"""
    if results['alerts']:
        summary += f"\n🚨 Alerts ({len(results['alerts'])}):\n"
        summary += chr(10).join(f"  • {a}" for a in results['alerts'])
    
    if results['errors']:
        summary += f"\n⚠️ Errors ({len(results['errors'])}):\n"
        summary += chr(10).join(f"  • {e}" for e in results['errors'][:3])
    
    print(summary)

if __name__ == "__main__":
    main()
