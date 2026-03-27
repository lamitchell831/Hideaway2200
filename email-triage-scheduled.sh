#!/bin/bash
# Smart Email Triage - Business Hours Only (8 AM - 4 PM ET)

# Check if we're in business hours (8 AM - 4 PM ET, Mon-Fri)
HOUR=$(date +%H)
DAY=$(date +%u)  # 1=Monday, 7=Sunday

if [ "$DAY" -gt 5 ]; then
    # Weekend - skip
    exit 0
fi

if [ "$HOUR" -lt 8 ] || [ "$HOUR" -ge 16 ]; then
    # Before 8 AM or after 4 PM - skip
    exit 0
fi

# Run the actual email triage
openclaw agent run --prompt "Process unread Gmail emails via IMAP. For each email: categorize as GENERAL, URGENT, BILL, NEWSLETTER, or SPAM. Create Todoist tasks for actionable items. Skip internal autostarusa.com emails unless marked urgent/critical/escalation. Archive newsletters. Send Telegram summary with counts and any urgent alerts. Log all actions."
