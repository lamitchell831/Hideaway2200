// Hideaway 2200 — Cloudflare Worker (Telegram relay)
//
// Required Worker secrets (set via `wrangler secret put` or the Cloudflare dashboard):
//   TELEGRAM_BOT_TOKEN  — the bot token from @BotFather
//   TELEGRAM_CHAT_ID    — destination chat ID
//
// Optional Worker vars:
//   ALLOWED_ORIGIN      — defaults to https://hideaway2200.com
//
// Do NOT hardcode secrets in this file or commit them to git.

const DEFAULT_ALLOWED_ORIGIN = 'https://hideaway2200.com';
const MAX_FIELD_LENGTHS = { name: 200, email: 320, message: 4000 };

export default {
  async fetch(request, env) {
    const allowedOrigin = (env && env.ALLOWED_ORIGIN) || DEFAULT_ALLOWED_ORIGIN;
    const requestOrigin = request.headers.get('Origin') || '';
    const originAllowed = requestOrigin === allowedOrigin;

    const corsHeaders = {
      'Access-Control-Allow-Origin': originAllowed ? allowedOrigin : '',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Vary': 'Origin',
    };

    if (request.method === 'OPTIONS') {
      if (!originAllowed) return new Response(null, { status: 403 });
      return new Response(null, { headers: corsHeaders });
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    if (!originAllowed) {
      return new Response(JSON.stringify({ success: false, error: 'Origin not allowed' }), {
        status: 403,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    if (!env || !env.TELEGRAM_BOT_TOKEN || !env.TELEGRAM_CHAT_ID) {
      return new Response(JSON.stringify({ success: false, error: 'Server not configured' }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    let payload;
    try {
      payload = await request.json();
    } catch {
      return new Response(JSON.stringify({ success: false, error: 'Invalid JSON' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const name = typeof payload.name === 'string' ? payload.name.trim() : '';
    const email = typeof payload.email === 'string' ? payload.email.trim() : '';
    const message = typeof payload.message === 'string' ? payload.message.trim() : '';

    if (!name || !email || !message) {
      return new Response(JSON.stringify({ success: false, error: 'Missing required fields' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    if (
      name.length > MAX_FIELD_LENGTHS.name ||
      email.length > MAX_FIELD_LENGTHS.email ||
      message.length > MAX_FIELD_LENGTHS.message
    ) {
      return new Response(JSON.stringify({ success: false, error: 'Field too long' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return new Response(JSON.stringify({ success: false, error: 'Invalid email' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const text = `🏡 Hideaway 2200 Inquiry\n\n👤 Name: ${name}\n📧 Email: ${email}\n\n💬 Message:\n${message}`;

    try {
      const tgResponse = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text }),
      });

      if (!tgResponse.ok) {
        return new Response(JSON.stringify({ success: false, error: 'Upstream error' }), {
          status: 502,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }

      return new Response(JSON.stringify({ success: true }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    } catch {
      return new Response(JSON.stringify({ success: false, error: 'Delivery failed' }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }
  },
};
