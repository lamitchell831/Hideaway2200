# BlueBubbles Server Setup

## Installation

1. Download BlueBubbles Server from: https://bluebubbles.app/downloads.html
   - Get the macOS version (.dmg)

2. Install and open BlueBubbles Server app

3. First-run setup:
   - It will ask for Full Disk Access (grant it)
   - Sign in with your Apple ID in the Messages app (keep Messages app running)
   - Set a secure password for the server
   - Note the server URL (usually http://[your-mac-ip]:12345)

4. Configure Settings:
   - Port: 12345 (or custom)
   - Password: [create strong password]
   - Enable "Start on Login"
   - Enable "Show in Menu Bar"

5. Test connection:
   - Open browser → http://localhost:12345
   - Should show BlueBubbles web interface

## OpenClaw Configuration

Add to `/Users/al/.openclaw/openclaw.json`:

```json
"channels": {
  "bluebubbles": {
    "enabled": true,
    "url": "http://192.168.1.xxx:12345",
    "password": "YOUR_BB_PASSWORD"
  }
}
```

Replace 192.168.1.xxx with your Mac Mini's actual IP.

Then restart OpenClaw gateway.

## Features You'll Get
- Send iMessages via OpenClaw
- Receive iMessages in Telegram
- Group chat support
- Read receipts
- Attachments (photos, etc.)

## Security Note
- Keep BlueBubbles password secure
- The server runs locally on your network
- iCloud Messages must be enabled on your Mac
