#!/usr/bin/env python3
"""Smart Email Triage for al.mitchell@autostarusa.com"""

import imaplib
import ssl
import email
from email.header import decode_header
import json
import re
from datetime import datetime, timedelta
import urllib.request
import urllib.error

# Config
IMAP_SERVER = "imap.gmail.com"
EMAIL = "al.mitchell@autostarusa.com"
PASSWORD = "twrp stsx tplg yvfe"
TODOIST_TOKEN = "67179992230c37477e22c7e230cad7d35ee10cc2"
TODOIST_PROJECT = "6gFqh9XqF8X8rff7"  # Work project
TELEGRAM_CHAT = "6038232911"

STATE_FILE = "/Users/al/.openclaw/workspace/gmail-state.json"

def decode_str(s):
    """Decode email header strings"""
    if s is None:
        return ""
    decoded = decode_header(s)
    result = ""
    for part, charset in decoded:
        if isinstance(part, bytes):
            try:
                result += part.decode(charset or 'utf-8', errors='replace')
            except:
                result += part.decode('utf-8', errors='replace')
        else:
            result += str(part)
    return result

def get_email_body(msg):
    """Extract text body from email"""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                try:
                    body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                    break
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
        except:
            pass
    return body[:500]  # First 500 chars as snippet

def categorize_email(subject, sender, body):
    """Categorize email based on content"""
    text = f"{subject} {sender} {body}".lower()
    
    # Check for newsletters/promotions first
    newsletter_keywords = ['unsubscribe', 'newsletter', 'promotions', 'marketing', 
                          'weekly digest', 'monthly update', 'noreply', 'no-reply']
    if any(kw in text for kw in newsletter_keywords):
        return 'NEWSLETTER'
    
    # Security alerts
    security_keywords = ['login', 'security alert', 'new device', 'password changed', 
                        'sign-in', 'suspicious activity']
    if any(kw in text for kw in security_keywords):
        return 'SECURITY'
    
    # Customer/Critical (but NOT internal)
    critical_keywords = ['outage', 'down', 'critical', 'escalation', 'complaint', 
                        'urgent', 'asap', 'dealer']
    if any(kw in text for kw in critical_keywords):
        return 'CUSTOMER_CRITICAL'
    
    # Approvals
    approval_keywords = ['approval', 'request', 'pending', 'approve', 'authorization']
    if any(kw in text for kw in approval_keywords):
        return 'APPROVAL'
    
    # Action items
    action_keywords = ['need', 'please', 'action required', 'follow up', 'todo']
    if any(kw in text for kw in action_keywords):
        return 'ACTION'
    
    return 'GENERAL'

def create_todoist_task(content, priority=1):
    """Create Todoist task. Priority: 1=normal, 2=medium, 3=high, 4=urgent"""
    url = "https://api.todoist.com/api/v1/tasks"
    headers = {
        "Authorization": f"Bearer {TODOIST_TOKEN}",
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "content": content,
        "project_id": TODOIST_PROJECT,
        "priority": priority,
        "due_string": "today"
    }).encode()
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            return result.get('id')
    except Exception as e:
        print(f"Todoist error: {e}")
        return None

def load_state():
    """Load email state"""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"processed": [], "lastRun": None}

def save_state(state):
    """Save email state"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, default=str)

def main():
    results = {
        "processed": 0,
        "tasks_created": 0,
        "categories": {},
        "emails": []
    }
    
    state = load_state()
    
    # Connect to IMAP
    context = ssl.create_default_context()
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, ssl_context=context)
    
    try:
        mail.login(EMAIL, PASSWORD)
        mail.select('INBOX')
        
        # Search for unread emails from last hour
        since_time = (datetime.now() - timedelta(hours=1)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(UNSEEN SINCE {since_time})')
        
        if status != 'OK' or not messages[0]:
            results["message"] = "No new unread emails from the last hour"
            print(json.dumps(results, indent=2))
            return results
        
        email_ids = messages[0].split()
        to_mark_read = []
        
        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            if status != 'OK':
                continue
            
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            subject = decode_str(msg['Subject'])
            sender = decode_str(msg['From'])
            date_str = decode_str(msg['Date'])
            body = get_email_body(msg)
            
            # Skip internal emails (unless urgent)
            if 'autostarusa.com' in sender.lower():
                urgent_in_internal = any(kw in f"{subject} {body}".lower() 
                                         for kw in ['urgent', 'critical', 'escalation'])
                if not urgent_in_internal:
                    to_mark_read.append(email_id)
                    results["categories"]['INTERNAL_SKIPPED'] = results["categories"].get('INTERNAL_SKIPPED', 0) + 1
                    continue
            
            # Categorize
            category = categorize_email(subject, sender, body)
            results["categories"][category] = results["categories"].get(category, 0) + 1
            
            email_info = {
                "subject": subject[:80],
                "sender": sender[:60],
                "category": category,
                "time": date_str[:50] if date_str else ""
            }
            results["emails"].append(email_info)
            
            # Handle based on category
            if category == 'NEWSLETTER':
                # Auto-mark read, no task
                to_mark_read.append(email_id)
                
            elif category == 'SECURITY':
                # Flag but don't task
                to_mark_read.append(email_id)
                
            elif category == 'CUSTOMER_CRITICAL':
                # High priority task
                task_content = f"🚨 [URGENT] {subject} from {sender.split('<')[0].strip()}"
                task_id = create_todoist_task(task_content, priority=4)
                if task_id:
                    results["tasks_created"] += 1
                to_mark_read.append(email_id)
                
            elif category == 'APPROVAL':
                # Medium priority task
                task_content = f"📧 [APPROVAL] {subject} from {sender.split('<')[0].strip()}"
                task_id = create_todoist_task(task_content, priority=3)
                if task_id:
                    results["tasks_created"] += 1
                to_mark_read.append(email_id)
                
            elif category in ('ACTION', 'GENERAL'):
                # Normal task
                task_content = f"📧 {subject} from {sender.split('<')[0].strip()}"
                task_id = create_todoist_task(task_content, priority=1)
                if task_id:
                    results["tasks_created"] += 1
                to_mark_read.append(email_id)
            
            results["processed"] += 1
        
        # Mark processed emails as read
        for email_id in to_mark_read:
            mail.store(email_id, '+FLAGS', '\\Seen')
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        results["error"] = str(e)
        print(json.dumps(results, indent=2))
        return results
    
    # Save state
    state["lastRun"] = datetime.now().isoformat()
    state["processed"].append({
        "time": datetime.now().isoformat(),
        "count": results["processed"],
        "tasks": results["tasks_created"]
    })
    save_state(state)
    
    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    main()
