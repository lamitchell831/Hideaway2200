#!/usr/bin/env python3
"""
Gmail + Todoist Sync Script
Check unread emails from today and create Todoist tasks for action items.
"""

import os
import json
import base64
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import requests

# Configuration
GMAIL_USER = "al.mitchell@autostarusa.com"
TODOIST_API_TOKEN = "67179992230c37477e22c7e230cad7d35ee10cc2"
TODOIST_WORK_PROJECT_ID = "6gFqh9XqF8X8rff7"
STATE_FILE = "gmail-state.json"

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

def get_gmail_service():
    """Build the Gmail API service."""
    creds = None
    # Try to load existing token
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.modify'
        ])
    
    if not creds:
        print("Error: No Gmail credentials found. Need OAuth token.")
        return None
    
    return build('gmail', 'v1', credentials=creds)

def get_unread_emails_from_today(service, state):
    """Get unread emails from today."""
    today = datetime.now().strftime('%Y/%m/%d')
    query = f'is:unread after:{today}'
    
    try:
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
        
        email_details = []
        for msg in messages:
            msg_id = msg['id']
            if msg_id not in state['processedEmails']:
                # Get full message details
                message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                
                # Extract subject and from
                headers = message['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                
                # Get snippet (preview)
                snippet = message.get('snippet', '')
                
                email_details.append({
                    'id': msg_id,
                    'subject': subject,
                    'from': from_email,
                    'snippet': snippet,
                    'threadId': msg['threadId']
                })
        
        return email_details
    except Exception as e:
        print(f"Error fetching emails: {e}")
        return []

def is_action_email(subject, snippet):
    """Determine if email contains action items."""
    action_keywords = [
        'action', 'task', 'todo', 'follow up', 'review', 'approve',
        'complete', 'submit', 'respond', 'reply', 'urgent', 'asap',
        'deadline', 'meeting', 'schedule', 'call', 'contact'
    ]
    
    text = (subject + ' ' + snippet).lower()
    return any(keyword in text for keyword in action_keywords)

def create_todoist_task(subject, email_id, thread_id):
    """Create a Todoist task in the Work project."""
    url = "https://api.todoist.com/api/v1/tasks"
    
    # Gmail link
    gmail_link = f"https://mail.google.com/mail/u/0/#inbox/{thread_id}"
    
    headers = {
        "Authorization": f"Bearer {TODOIST_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "content": subject,
        "description": f"From email: {gmail_link}",
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
    print("Gmail + Todoist Sync")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Load state
    state = load_state()
    print(f"\nLoaded state. {len(state['processedEmails'])} emails already processed.")
    
    # Get Gmail service
    service = get_gmail_service()
    if not service:
        print("\n⚠️  Gmail authentication required.")
        print("Please run the OAuth flow first:")
        print("  python3 gmail_auth.py")
        return []
    
    # Get unread emails from today
    print("\nFetching unread emails from today...")
    emails = get_unread_emails_from_today(service, state)
    print(f"Found {len(emails)} new unread emails from today.")
    
    tasks_created = []
    
    for email in emails:
        print(f"\n📧 {email['subject']}")
        print(f"   From: {email['from']}")
        
        # Check if it's an action email
        if is_action_email(email['subject'], email['snippet']):
            print("   ✓ Contains action items - creating Todoist task...")
            success, task_id = create_todoist_task(
                email['subject'], 
                email['id'], 
                email['threadId']
            )
            if success:
                tasks_created.append({
                    'subject': email['subject'],
                    'from': email['from'],
                    'task_id': task_id
                })
                print("   ✓ Task created successfully!")
            else:
                print("   ✗ Failed to create task")
        else:
            print("   - No action items detected, skipping")
        
        # Mark as processed regardless
        mark_email_processed(state, email['id'])
    
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