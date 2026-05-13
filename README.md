# Hideaway 2200 Website Documentation

## Overview

**Live URL:** https://hideaway2200.com  
**Repository:** https://github.com/lamitchell831/Hideaway2200  
**Technology Stack:** Static HTML, Tailwind CSS, Vanilla JavaScript  
**Hosting:** cPanel (Namecheap) with GitHub Actions auto-deployment

---

## Table of Contents

1. [Architecture](#architecture)
2. [File Structure](#file-structure)
3. [Dependencies](#dependencies)
4. [Design System](#design-system)
5. [Features](#features)
6. [Chat Widget](#chat-widget)
7. [Deployment](#deployment)
8. [SEO Configuration](#seo-configuration)
9. [Maintenance](#maintenance)

---

## Architecture

### Static Site Architecture

The Hideaway 2200 website is a **static HTML website** — no backend server, no database, no CMS. This design choice provides:

- **Security**: No attack surface (no SQL injection, no server-side vulnerabilities)
- **Speed**: Files served directly from web server, no processing overhead
- **Reliability**: No server crashes, no database connection issues
- **Cost**: Minimal hosting requirements

### Hosting Stack

```
┌─────────────────────────────────────────┐
│           User Browser                  │
└─────────────┬───────────────────────────┘
              │ HTTPS
              ▼
┌─────────────────────────────────────────┐
│         GoDaddy DNS                     │
│    (hideaway2200.com domain)          │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│      Namecheap cPanel Hosting             │
│    (Apache/LiteSpeed Web Server)        │
│         public_html/                    │
│    ┌──────────────────────┐             │
│    │   index.html         │             │
│    │   guidebook.html     │             │
│    │   chat-widget.js     │             │
│    │   hero-bg.jpg        │             │
│    └──────────────────────┘             │
└─────────────────────────────────────────┘
```

---

## File Structure

```
Hideaway2200/
│
├── index.html              # Main landing page
├── guidebook.html          # Guest guidebook (HTML version)
├── chat-widget.js          # Live chat widget (no secrets — calls Worker)
├── hero-bg.jpg             # Hero background image (Blue Ridge Mountains)
│
├── robots.txt              # SEO: Search engine crawling rules
├── sitemap.xml             # SEO: Site structure for search engines
├── SEO-CHECKLIST.md        # SEO launch checklist
│
├── .github/
│   └── workflows/
│       ├── deploy-cpanel.yml      # GitHub Actions auto-deployment
│       └── staging-deploy.yml     # Staging deployment workflow
│
├── cloudflare-worker.js    # Cloudflare Worker (Telegram relay; reads secrets from env)
└── README.md
```

> Optional/expected-but-not-present files referenced elsewhere (e.g. `hideaway2200-icon.svg`, logo SVGs, `.htaccess`) are not currently tracked in this repo. Add them in `public_html/` on the server or commit them as needed.

---

## Dependencies

### External Dependencies (CDN)

| Dependency | Purpose | URL |
|------------|---------|-----|
| **Tailwind CSS** | Utility-first CSS framework | `https://cdn.tailwindcss.com` |
| **Tailwind Config** | Custom color palette & fonts | Inline `<script>` block |
| **Google Fonts** | Typography (Cormorant Garamond, Inter) | `https://fonts.googleapis.com` |
| **Font Awesome** | Icons | `https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0` |

### Tailwind Configuration

Custom theme configuration embedded in HTML:

```javascript
tailwind.config = {
    theme: {
        extend: {
            colors: {
                'forest': '#2d3a2d',
                'forest-light': '#3d4a3d',
                'sage': '#5a6b5a',
                'sage-light': '#6b7d6b',
                'cream': '#f8f6f3',
                'cream-dark': '#e8e6e1',
                'slate-blue': '#7a9db0',
                'slate-blue-dark': '#5a7d90'
            },
            fontFamily: {
                serif: ['Cormorant Garamond', 'serif'],
                sans: ['Inter', 'sans-serif']
            }
        }
    }
}
```

### Third-Party Services

| Service | Purpose | Data Shared |
|---------|---------|-------------|
| **Telegram Bot API** | Chat widget message delivery | Visitor name, email, message |
| **Cloudflare Workers** | CORS proxy for Telegram | Message content (temporarily) |
| **Google Fonts** | Typography | IP address (standard) |
| **Font Awesome CDN** | Icons | IP address (standard) |

---

## Design System

### Color Palette

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| **Forest** | `#2d3a2d` | Primary text, headings, dark backgrounds |
| **Forest Light** | `#3d4a3d` | Hover states, secondary elements |
| **Sage** | `#5a6b5a` | Secondary text, borders, accents |
| **Sage Light** | `#6b7d6b` | Hover states, subtle accents |
| **Cream** | `#f8f6f3` | Light backgrounds, cards |
| **Cream Dark** | `#e8e6e1` | Borders, dividers, subtle backgrounds |
| **Slate Blue** | `#7a9db0` | Links, accent buttons, highlights |
| **Slate Blue Dark** | `#5a7d90` | Link hover states |

### Typography

| Element | Font Family | Weight | Size |
|---------|-------------|--------|------|
| **H1 (Hero)** | Cormorant Garamond | 500 | 48-72px (responsive) |
| **H2 (Section)** | Cormorant Garamond | 500 | 32-36px |
| **H3 (Cards)** | Cormorant Garamond | 600 | 20-24px |
| **Body** | Inter | 300-400 | 14-18px |
| **Button** | Inter | 500 | 14-16px |
| **Caption** | Inter | 400 | 12-14px |

### Responsive Breakpoints

| Breakpoint | Tailwind Class | Target Devices |
|------------|---------------|----------------|
| Mobile | Default | < 640px |
| Tablet | `sm:` | 640px+ |
| Desktop | `md:` | 768px+ |
| Large Desktop | `lg:` | 1024px+ |
| XL | `xl:` | 1280px+ |

---

## Features

### 1. Hero Section

- **Full-height background image** (Blue Ridge Mountains)
- **Animated fade-in** on page load (`animate-fade-in`)
- **Call-to-action buttons**: Book Now, View Guidebook
- **Gradient overlay** for text readability

### 2. Property Gallery

- **Responsive grid**: 1 col mobile → 2 col tablet → 3 col desktop
- **Hover effects**: Scale + shadow on cards
- **Images**: Lazy loading via `loading="lazy"`

### 3. Amenity Grid

- **Icons**: Font Awesome
- **Cards**: Cream background with hover lift
- **Responsive**: 2 col mobile → 4 col desktop

### 4. Booking Section

- **Direct booking emphasis**: "Book direct & save"
- **OTA comparison**: Airbnb, Vrbo with pricing
- **Trust badges**: Secure payment, instant confirmation

### 5. Location Section

- **Proximity highlights**: 10 min to downtown, 5 min to Blue Ridge Parkway
- **Google Maps link**: Opens in new tab
- **Address privacy**: General area only (exact address post-booking)

### 6. FAQ Accordion

- **Interactive**: Click to expand/collapse
- **Categories**: Booking, amenities, location, policies
- **Smooth animation**: CSS transition

---

## Chat Widget

### Architecture

The chat widget allows visitors to send messages that are delivered to your Telegram.

```
Visitor Browser
      │
      │ 1. Fills form (name, email, message)
      │ 2. Clicks Send
      ▼
┌─────────────────────┐
│  chat-widget.js     │
│  - Validates input  │
│  - Formats message  │
└──────────┬──────────┘
           │
           │ POST to Cloudflare Worker
           │ (avoids CORS issues)
           ▼
┌─────────────────────┐
│  Cloudflare Worker  │
│  (CORS proxy)       │
│  - Receives POST    │
│  - Sends to Telegram│
└──────────┬──────────┘
           │
           │ Telegram Bot API
           ▼
┌─────────────────────┐
│  Telegram Bot       │
│  @Hideaway2200_bot  │
│  - Delivers message │
│  - You receive it   │
└─────────────────────┘
```

### Configuration

**Frontend widget configuration** (in `chat-widget.js`):
```javascript
const CONFIG = {
    workerUrl: 'https://hideaway2200-chat.lamitchell831.workers.dev',
    welcomeMessage: '...'
};
```

The widget contains **no secrets**. It only knows the Worker URL — the bot token and chat ID live as Cloudflare Worker secrets.

**Cloudflare Worker secrets** (set via `wrangler secret put` or the Cloudflare dashboard, never committed to git):

| Secret | Purpose |
|--------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token issued by @BotFather |
| `TELEGRAM_CHAT_ID`   | Destination Telegram chat/user ID |
| `ALLOWED_ORIGIN` *(optional var)* | Allowed CORS origin, defaults to `https://hideaway2200.com` |

Example setup:

```bash
wrangler secret put TELEGRAM_BOT_TOKEN   # paste token when prompted
wrangler secret put TELEGRAM_CHAT_ID     # paste chat id when prompted
```

**Cloudflare Worker:**
- Endpoint: `https://hideaway2200-chat.lamitchell831.workers.dev/`
- Function: Receives POST from widget, validates input, forwards to Telegram API
- CORS: Locked to `https://hideaway2200.com` (configurable via `ALLOWED_ORIGIN`)
- Validation: Requires non-empty name/email/message, rejects malformed email, caps field lengths

> **Security note:** If the bot token has ever been committed to this repo or pasted in documentation, rotate it via @BotFather and update the `TELEGRAM_BOT_TOKEN` secret. The previous token in git history must be considered compromised.

### Message Flow

1. **Visitor** enters name, email, message
2. **Validation**: Both name and email required
3. **Formatting**: Message includes name, email, timestamp
4. **Delivery**: Sent via Cloudflare Worker to Telegram
5. **Receipt**: You receive message on Telegram
6. **Response**: You reply via email/phone (not in widget)

### Privacy Notes

- **No message storage**: Messages go directly to Telegram, not stored on website
- **No visitor tracking**: No cookies, no analytics on chat
- **SSL encrypted**: All communications over HTTPS

---

## Deployment

### GitHub Actions Auto-Deployment

**File:** `.github/workflows/deploy-cpanel.yml`

**Triggers:**
- Push to `main` branch
- Manual dispatch

**Process:**
1. Checkout repository
2. Upload files to cPanel via FTP
3. Deploy to `public_html/`

**Required Secrets (GitHub Settings → Secrets):**
| Secret Name | Value |
|-------------|-------|
| `CPANEL_FTP_HOST` | `ftp.hideaway2200.com` |
| `CPANEL_FTP_USERNAME` | `public_html@hideaway2200.com` |
| `CPANEL_FTP_PASSWORD` | [Your FTP password] |

### Manual Deployment

```bash
# Using FTP/SFTP
sftp public_html@hideaway2200.com
put index.html
put guidebook.html
put chat-widget.js
put hero-bg.jpg
bye
```

---

## SEO Configuration

### Meta Tags (All Pages)

```html
<!-- Basic -->
<title>Hideaway 2200 | Tiny House Rental Asheville NC | Sleeps 8</title>
<meta name="description" content="Modern tiny house on a private pond near Asheville, NC. Sleeps 8...">
<meta name="keywords" content="tiny house rental asheville nc, cabin rental, vacation rental...">

<!-- Open Graph (Facebook) -->
<meta property="og:title" content="Hideaway 2200 | Tiny House Rental Asheville NC">
<meta property="og:description" content="Modern tiny house sleeping 8 on a private pond...">
<meta property="og:image" content="https://hideaway2200.com/og-image.jpg">

<!-- Twitter Cards -->
<meta property="twitter:title" content="Hideaway 2200 | Tiny House Rental Asheville NC">
<meta property="twitter:description" content="Modern tiny house sleeping 8...">
```

### Structured Data (Schema.org)

```json
{
    "@context": "https://schema.org",
    "@type": "LodgingBusiness",
    "name": "Hideaway 2200",
    "description": "Modern tiny house rental in Asheville, NC",
    "address": {
        "@type": "PostalAddress",
        "addressLocality": "Asheville",
        "addressRegion": "NC"
    }
}
```

### SEO Files

| File | Purpose |
|------|---------|
| `robots.txt` | Allows all crawling, points to sitemap |
| `sitemap.xml` | Lists all pages for search engines |

---

## Maintenance

### Regular Tasks

| Task | Frequency | Notes |
|------|-----------|-------|
| **Backup** | Monthly | GitHub repo is backup |
| **Update logo** | As needed | Replace SVG files |
| **Update photos** | Seasonally | Optimize images (< 500KB) |
| **Check links** | Quarterly | Use link checker tool |
| **Review analytics** | Monthly | Google Search Console |

### Updating Content

**To update text:**
1. Edit `index.html` or `guidebook.html`
2. Commit to GitHub
3. Auto-deploys via GitHub Actions

**To update images:**
1. Replace file in repository
2. Keep same filename OR update HTML reference
3. Commit and push

**To update chat widget:**
1. Edit `chat-widget.js`
2. Test locally
3. Commit and push

### Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Chat not working | CORS or Worker down | Check Cloudflare Worker status |
| Site not loading | DNS issue | Verify GoDaddy DNS points to cPanel |
| Changes not showing | CDN cache | Clear browser cache (Ctrl+Shift+R) |
| Images broken | Wrong path | Check file names match exactly |
| Fonts not loading | Google Fonts blocked | Check network, fallback to system fonts |

---

## Security Considerations

### Static Site Security

✅ **Advantages:**
- No database to hack
- No server-side code to exploit
- No user input processing (except chat widget)

⚠️ **Considerations:**
- **XSS**: Minimal risk (no user-generated content displayed)
- **Clickjacking**: Add X-Frame-Options header
- **CORS**: Properly configured on Cloudflare Worker

### Recommended .htaccess

```apache
# Security Headers
Header always set X-Frame-Options "SAMEORIGIN"
Header always set X-XSS-Protection "1; mode=block"
Header always set X-Content-Type-Options "nosniff"
Header always set Referrer-Policy "strict-origin-when-cross-origin"

# Hide server version
ServerSignature Off

# Disable directory listing
Options -Indexes
```

---

## Support & Contact

**Website Issues:** Check this documentation first, then review GitHub repository
**Chat Widget:** Verify Telegram bot is running, check Cloudflare Worker logs
**Hosting:** Namecheap cPanel support
**Domain:** GoDaddy support

---

## Changelog

### March 27, 2026
- ✅ Website launched
- ✅ Chat widget implemented with Telegram integration
- ✅ Auto-deployment via GitHub Actions
- ✅ SEO optimization complete

---

*Last Updated: March 27, 2026*
*Documentation Version: 1.0*