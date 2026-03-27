#!/usr/bin/env python3
"""
Gmail to Todoist Sync Script
Checks Gmail for unread emails from today and creates Todoist tasks for action items.
"""

import os
import json
import base64
import re
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# Config
GMAIL_USER = "al.mitchell@autostarusa.com"
TODOIST_API_TOKEN = "67179992230c37477e22c7e230cad7d35ee10cc2"
TODOIST_WORK_PROJECT_ID = "6gFqh9XqF8X8rff7"
STATE_FILE = "gmail-state.json"

def load_state():
    """Load processed emails state."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"processedEmails": [], "lastCheck": ""}

def save_state(state):
    """Save processed emails state."""
    state["lastCheck"] = datetime.now(timezone.utc).isoformat()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def todoist_request(endpoint, method="GET", data=None):
    """Make a request to Todoist API."""
    url = f"https://api.todoist.com/api/v1/{endpoint}"
    headers = {
        "Authorization": f"Bearer {TODOIST_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    req = Request(url, method=method, headers=headers)
    if data:
        req.data = json.dumps(data).encode('utf-8')
    
    try:
        with urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except HTTPError as e:
        print(f"Todoist API error: {e.code} - {e.read().decode('utf-8')}")
        return None

def create_todoist_task(content, description=""):
    """Create a Todoist task in the Work project."""
    data = {
        "content": content,
        "description": description,
        "project_id": TODOIST_WORK_PROJECT_ID
    }
    return todoist_request("tasks", method="POST", data=data)

def get_gmail_auth_token():
    """
    Get Gmail access token using OAuth device flow or refresh token.
    For this script, we'll use a refresh token if available.
    """
    token_file = "gmail-token.json"
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            token_data = json.load(f)
            return token_data.get("access_token")
    return None

def get_today_date():
    """Get today's date in Gmail search format (YYYY/MM/DD)."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y/%m/%d")

def detect_action_items(subject, snippet, body=""):
    """
    Detect if an email contains action items for Overlord.
    Looks for keywords like: action, task, todo, deadline, due, review, approve, please
    """
    text = f"{subject} {snippet} {body}".lower()
    
    action_keywords = [
        "action", "task", "todo", "deadline", "due",
        "review", "approve", "please", "need you to",
        "can you", "could you", "follow up", "reminder",
        "urgent", "asap", "required", "requested",
        "prepare", "send", "update", "schedule"
    ]
    
    # Skip automated/noreply emails
    skip_patterns = [
        r"no[-\s]?reply",
        r"noreply",
        r"do[-\s]?not[-\s]?reply",
        r"notification@",
        r"alert@",
        r"billing@",
        r"receipt",
        r"invoice",
        r"shipping",
        r"tracking",
        r"order",
        r"subscription",
        r"marketing",
        r"promotional",
        r"unsubscribe",
        r"digest",
        r"weekly",
        r"monthly",
        r"newsletter"
    ]
    
    for pattern in skip_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False
    
    for keyword in action_keywords:
        if keyword in text:
            return True
    
    return False

def check_gmail_via_imap():
    """
    Check Gmail using IMAP as fallback.
    Returns list of email dicts with id, subject, from, snippet.
    """
    try:
        import imaplib
        import email
        from email import policy
        
        # Connect to Gmail IMAP
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        
        # Check for app password in environment or token file
        app_password = os.environ.get("GMAIL_APP_PASSWORD")
        if not app_password:
            # Try to read from credentials file
            creds_file = "gmail-credentials.json"
            if os.path.exists(creds_file):
                with open(creds_file, 'r') as f:
                    creds = json.load(f)
                    app_password = creds.get("app_password")
        
        if not app_password:
            print("No Gmail app password found")
            return []
        
        imap.login(GMAIL_USER, app_password)
        imap.select("inbox")
        
        # Search for unread emails from today
        today = datetime.now(timezone.utc)
        date_str = today.strftime("%d-%b-%Y")
        
        # Search for unread emails
        _, messages = imap.search(None, f'(UNSEEN SINCE "{date_str}")')
        
        emails = []
        for msg_id in messages[0].split():
            if not msg_id:
                continue
                
            _, msg_data = imap.fetch(msg_id, "(RFC822)")
            raw_email = msg_data[0][1]
            
            # Parse email
            msg = email.message_from_bytes(raw_email, policy=policy.default)
            
            subject = msg["Subject"] or "(No Subject)"
            from_addr = msg["From"] or "Unknown"
            email_id = msg["Message-ID"] or str(msg_id, 'utf-8')
            
            # Get snippet (first 500 chars of body)
            snippet = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        try:
                            body = part.get_content()
                            snippet = body[:500]
                            break
                        except:
                            pass
            else:
                try:
                    body = msg.get_content()
                    snippet = body[:500]
                except:
                    pass
            
            emails.append({
                "id": email_id,
                "subject": subject,
                "from": from_addr,
                "snippet": snippet,
                "gmail_id": msg_id.decode('utf-8')
            })
        
        imap.close()
        imap.logout()
        
        return emails
        
    except Exception as e:
        print(f"IMAP error: {e}")
        return []

def check_gmail_via_oauth():
    """
    Check Gmail using OAuth and REST API.
    """
    access_token = get_gmail_auth_token()
    if not access_token:
        return []
    
    try:
        # Search for unread emails from today
        today = get_today_date()
        query = f"is:unread after:{today}"
        
        url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages?q={query}"
        req = Request(url, headers={"Authorization": f"Bearer {access_token}"})
        
        with urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            messages = data.get("messages", [])
        
        emails = []
        for msg in messages:
            msg_id = msg["id"]
            
            # Get message details
            detail_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}"
            detail_req = Request(detail_url, headers={"Authorization": f"Bearer {access_token}"})
            
            with urlopen(detail_req) as response:
                msg_data = json.loads(response.read().decode('utf-8'))
            
            # Extract headers
            headers = {h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])}
            
            subject = headers.get("Subject", "(No Subject)")
            from_addr = headers.get("From", "Unknown")
            
            # Get snippet
            snippet = msg_data.get("snippet", "")
            
            # Get body
            body = ""
            payload = msg_data.get("payload", {})
            if "parts" in payload:
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/plain":
                        data = part.get("body", {}).get("data", "")
                        if data:
                            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                            break
            
            emails.append({
                "id": msg_id,
                "subject": subject,
                "from": from_addr,
                "snippet": snippet,
                "body": body[:500]
            })
        
        return emails
        
    except Exception as e:
        print(f"OAuth Gmail error: {e}")
        return []

def main():
    """Main function to sync Gmail to Todoist."""
    print("Starting Gmail to Todoist sync...")
    
    # Load state
    state = load_state()
    processed_ids = set(state.get("processedEmails", []))
    
    # Check Gmail
    print("Checking Gmail...")
    emails = check_gmail_via_oauth()
    
    if not emails:
        # Fallback to IMAP
        emails = check_gmail_via_imap()
    
    if not emails:
        print("No new unread emails found or unable to access Gmail.")
        save_state(state)
        print("\nNo new tasks created.")
        return
    
    print(f"Found {len(emails)} unread emails from today.")
    
    # Process emails
    tasks_created = []
    new_processed_ids = []
    
    for email_data in emails:
        email_id = email_data.get("id", email_data.get("gmail_id"))
        
        if email_id in processed_ids:
            print(f"Skipping already processed email: {email_data['subject']}")
            continue
        
        subject = email_data.get("subject", "(No Subject)")
        from_addr = email_data.get("from", "Unknown")
        snippet = email_data.get("snippet", "")
        body = email_data.get("body", "")
        
        print(f"Processing: {subject} (from: {from_addr})")
        
        # Check if this contains action items
        if detect_action_items(subject, snippet, body):
            # Create Todoist task
            task_content = f"📧 {subject}"
            task_desc = f"From: {from_addr}\n\nSnippet: {snippet[:200]}...\n\nEmail ID: {email_id}"
            
            result = create_todoist_task(task_content, task_desc)
            
            if result:
                tasks_created.append({
                    "subject": subject,
                    "from": from_addr,
                    "todoist_id": result.get("id")
                })
                print(f"  ✓ Created Todoist task: {subject}")
            else:
                print(f"  ✗ Failed to create Todoist task")
        else:
            print(f"  - No action items detected")
        
        # Mark as processed
        new_processed_ids.append(email_id)
    
    # Update state
    state["processedEmails"].extend(new_processed_ids)
    save_state(state)
    
    # Print summary
    print(f"\n{'='*50}")
    print("SYNC SUMMARY")
    print(f"{'='*50}")
    print(f"Emails checked: {len(emails)}")
    print(f"Tasks created: {len(tasks_created)}")
    
    if tasks_created:
        print("\nTasks created:")
        for task in tasks_created:
            print(f"  • {task['subject']}")
            print(f"    From: {task['from']}")
    else:
        print("\nNo new tasks created (no action items found).")

if __name__ == "__main__":
    main()
