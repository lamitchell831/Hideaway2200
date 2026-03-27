#!/usr/bin/env python3
"""Debug IMAP connection and inbox contents."""

import imaplib
import email
import ssl
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
EMAIL_USER = "al.mitchell@autostarusa.com"
EMAIL_PASS = "twrp stsx tplg yvfe"

try:
    context = ssl.create_default_context()
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT, ssl_context=context)
    mail.login(EMAIL_USER, EMAIL_PASS)
    
    # List folders
    print("=== Folders ===")
    status, folders = mail.list()
    for f in folders[:5]:
        print(f.decode())
    
    # Select inbox
    mail.select("INBOX")
    
    # Check ALL emails
    print("\n=== All Emails ===")
    status, messages = mail.search(None, "ALL")
    all_ids = messages[0].split()
    print(f"Total emails in inbox: {len(all_ids)}")
    
    # Check unread
    print("\n=== Unread Emails ===")
    status, messages = mail.search(None, "UNSEEN")
    unread_ids = messages[0].split() if messages[0] else []
    print(f"Unread emails: {len(unread_ids)}")
    
    # Check recent
    print("\n=== Recent Emails (last 24 hours) ===")
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%d-%b-%Y")
    status, messages = mail.search(None, "SINCE", cutoff)
    recent_ids = messages[0].split() if messages[0] else []
    print(f"Emails since {cutoff}: {len(recent_ids)}")
    
    # Show first few recent
    for msg_id in recent_ids[:3]:
        status, msg_data = mail.fetch(msg_id, "(RFC822)")
        if status == "OK":
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            subject = msg.get("Subject", "No Subject")
            sender = msg.get("From", "Unknown")
            date = msg.get("Date", "")
            seen = "\\Seen" in str(msg.get("Flags", ""))
            print(f"  - [{msg_id.decode()}] {subject[:50]}... | From: {sender[:30]} | Seen: {not seen}")
    
    mail.logout()
    print("\n=== Connection successful ===")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
