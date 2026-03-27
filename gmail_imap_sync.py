#!/usr/bin/env python3
"""
Gmail + Todoist Sync Script (IMAP Version)
Check unread emails from today and create Todoist tasks for action items.
Uses IMAP with app password.
"""

import os
import json
import imaplib
import email
from datetime import datetime, date
import requests

# Configuration
GMAIL_USER = "al.mitchell@autostarusa.com"
GMAIL_PASSWORD = "twrp stsx tplg yvfe"  # App password from TOOLS.md
TODOIST_API_TOKEN = "67179992230c37477e22c7e230cad7d35ee10cc2"
TODOIST_WORK_PROJECT_ID = "6gFqh9XqF8X8rff7"
STATE_FILE = "/Users/al/.openclaw/workspace/gmail-state.json"

def load_state():
    """Load the state file with processed email IDs."""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"processedEmails": [], "lastCheck": None}

def save_state(state):
    """Save the state file."""
    state["lastCheck"] = datetime.utcnow().isoformat()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_unread_emails_from_today(state):
    """Get unread emails from today using IMAP."""
    try:
        # Connect to Gmail IMAP
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASSWORD)
        mail.select("inbox")
        
        # Search for unread emails from today
        today = date.today().strftime("%d-%b-%Y")
        result, data = mail.search(None, f'(UNSEEN SINCE "{today}")')
        
        if result != 'OK':
            print(f"Search failed: {result}")
            return []
        
        email_ids = data[0].split()
        print(f"Found {len(email_ids)} unread email IDs from today")
        
        email_details = []
        for email_id in email_ids:
            email_id_str = email_id.decode('utf-8')
            
            # Skip already processed
            if email_id_str in state['processedEmails']:
                continue
            
            # Fetch email
            result, msg_data = mail.fetch(email_id, "(RFC822)")
            if result != 'OK':
                continue
            
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Extract info
            subject = msg.get('Subject', 'No Subject')
            from_email = msg.get('From', 'Unknown')
            
            # Get snippet (first 200 chars of body)
            snippet = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            snippet = body[:200].replace('\n', ' ').replace('\r', '')
                            break
                        except:
                            pass
            else:
                try:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                    snippet = body[:200].replace('\n', ' ').replace('\r', '')
                except:
                    pass
            
            email_details.append({
                'id': email_id_str,
                'subject': subject,
                'from': from_email,
                'snippet': snippet
            })
        
        mail.logout()
        return email_details
        
    except Exception as e:
        print(f"IMAP error: {e}")
        return []

def is_action_email(subject, snippet):
    """Determine if email contains action items."""
    action_keywords = [
        'action', 'task', 'todo', 'follow up', 'review', 'approve',
        'complete', 'submit', 'respond', 'reply', 'urgent', 'asap',
        'deadline', 'meeting', 'schedule', 'call', 'contact',
        'needs', 'please', 'can you', 'could you', 'would you'
    ]
    
    text = (subject + ' ' + snippet).lower()
    return any(keyword in text for keyword in action_keywords)

def create_todoist_task(subject, email_id, from_email):
    """Create a Todoist task in the Work project."""
    url = "https://api.todoist.com/api/v1/tasks"
    
    headers = {
        "Authorization": f"Bearer {TODOIST_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "content": subject,
        "description": f"From: {from_email}\nGmail search: from:{from_email} subject:{subject}",
        "project_id": TODOIST_WORK_PROJECT_ID,
        "labels": ["gmail"]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return True, response.json().get('id')
        else:
            print(f"Todoist API error: {response.status_code} - {response.text}")
            return False, None
    except Exception as e:
        print(f"Error creating Todoist task: {e}")
        return False, None

def mark_email_processed(state, email_id):
    """Mark an email as processed."""
    if email_id not in state['processedEmails']:
        state['processedEmails'].append(email_id)

def main():
    print("=" * 60)
    print("Gmail + Todoist Sync (IMAP)")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Load state
    state = load_state()
    print(f"\nLoaded state. {len(state['processedEmails'])} emails already processed.")
    
    # Get unread emails from today
    print("\nFetching unread emails from today via IMAP...")
    emails = get_unread_emails_from_today(state)
    print(f"Found {len(emails)} new unread emails from today.")
    
    tasks_created = []
    
    for email_data in emails:
        print(f"\n📧 {email_data['subject']}")
        print(f"   From: {email_data['from']}")
        
        # Check if it's an action email
        if is_action_email(email_data['subject'], email_data['snippet']):
            print("   ✓ Contains action items - creating Todoist task...")
            success, task_id = create_todoist_task(
                email_data['subject'], 
                email_data['id'], 
                email_data['from']
            )
            if success:
                tasks_created.append({
                    'subject': email_data['subject'],
                    'from': email_data['from'],
                    'task_id': task_id
                })
                print("   ✓ Task created successfully!")
            else:
                print("   ✗ Failed to create task")
        else:
            print("   - No action items detected, skipping")
        
        # Mark as processed regardless
        mark_email_processed(state, email_data['id'])
    
    # Save state
    save_state(state)
    print(f"\n✓ State saved. {len(state['processedEmails'])} emails now marked as processed.")
    
    return tasks_created

if __name__ == "__main__":
    tasks = main()
    
    # Output summary as JSON for the caller
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(json.dumps({
        "tasks_created": len(tasks),
        "tasks": tasks
    }, indent=2))