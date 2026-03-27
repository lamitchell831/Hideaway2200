// Hideaway 2200 Chat Widget
// Forwards messages to Telegram bot

(function() {
  // Configuration - UPDATE THESE
  const CONFIG = {
    botToken: '8659177571:AAFuI7vv9My6qchdQ167hNObUJnqEHvXo1w',  // BotFather token
    chatId: '6038232911',              // Your Telegram ID
    welcomeMessage: 'Hi! Questions about Hideaway 2200? I\'ll connect you with the host.',
    offlineMessage: 'Thanks for your message! I\'ll get back to you shortly.'
  };

  // Helper functions defined first
  function hhFormatTime() {
    return new Date().toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
  }

  // Create widget HTML - use placeholder for time, fill in after functions load
  const widgetHTML = `
    <div id="hh-chat-widget" class="hh-chat-closed">
      <div class="hh-chat-header">
        <span class="hh-chat-title">💬 Chat with Host</span>
        <button class="hh-chat-toggle" onclick="hhChatToggle()">−</button>
      </div>
      <div class="hh-chat-body">
        <div class="hh-chat-messages" id="hh-messages">
          <div class="hh-message hh-message-bot">
            <div class="hh-message-text">${CONFIG.welcomeMessage}</div>
            <div class="hh-message-time" id="hh-welcome-time">${hhFormatTime()}</div>
          </div>
        </div>
        <div class="hh-chat-input-area">
          <input type="text" id="hh-input" placeholder="Type your message..." 
                 onkeypress="if(event.key==='Enter')hhChatSend()">
          <button onclick="hhChatSend()">Send</button>
        </div>
      </div>
    </div>
    <button id="hh-chat-button" onclick="hhChatToggle()" class="hh-chat-button-closed">
      💬
    </button>
  `;

  // Create widget styles
  const widgetCSS = `
    <style>
      #hh-chat-widget {
        position: fixed;
        bottom: 80px;
        right: 20px;
        width: 320px;
        height: 400px;
        background: #f8f6f3;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.15);
        display: flex;
        flex-direction: column;
        overflow: hidden;
        font-family: 'Inter', -apple-system, sans-serif;
        z-index: 9999;
        transition: transform 0.3s ease, opacity 0.3s ease;
      }
      
      #hh-chat-widget.hh-chat-closed {
        transform: translateY(20px);
        opacity: 0;
        pointer-events: none;
      }
      
      .hh-chat-header {
        background: #2d3a2d;
        color: #f8f6f3;
        padding: 16px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .hh-chat-title {
        font-weight: 500;
        font-size: 15px;
      }
      
      .hh-chat-toggle {
        background: none;
        border: none;
        color: #f8f6f3;
        font-size: 20px;
        cursor: pointer;
        padding: 0;
        width: 24px;
        height: 24px;
        line-height: 24px;
      }
      
      .hh-chat-body {
        flex: 1;
        display: flex;
        flex-direction: column;
        overflow: hidden;
      }
      
      .hh-chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      
      .hh-message {
        max-width: 85%;
        padding: 12px 16px;
        border-radius: 16px;
        font-size: 14px;
        line-height: 1.5;
      }
      
      .hh-message-bot {
        background: #e8e6e1;
        color: #2d3a2d;
        align-self: flex-start;
        border-bottom-left-radius: 4px;
      }
      
      .hh-message-user {
        background: #2d3a2d;
        color: #f8f6f3;
        align-self: flex-end;
        border-bottom-right-radius: 4px;
      }
      
      .hh-message-time {
        font-size: 11px;
        opacity: 0.6;
        margin-top: 4px;
      }
      
      .hh-chat-input-area {
        padding: 12px 16px;
        background: #fff;
        border-top: 1px solid #e8e6e1;
        display: flex;
        gap: 8px;
      }
      
      .hh-chat-input-area input {
        flex: 1;
        padding: 10px 14px;
        border: 1px solid #d4d0c8;
        border-radius: 20px;
        font-size: 14px;
        outline: none;
        font-family: inherit;
      }
      
      .hh-chat-input-area input:focus {
        border-color: #2d3a2d;
      }
      
      .hh-chat-input-area button {
        background: #2d3a2d;
        color: #f8f6f3;
        border: none;
        padding: 10px 20px;
        border-radius: 20px;
        font-size: 14px;
        cursor: pointer;
        font-weight: 500;
        transition: background 0.2s;
      }
      
      .hh-chat-input-area button:hover {
        background: #3d4a3d;
      }
      
      #hh-chat-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 56px;
        height: 56px;
        border-radius: 28px;
        background: #2d3a2d;
        color: #f8f6f3;
        border: none;
        font-size: 24px;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 9998;
        transition: transform 0.2s, background 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      
      #hh-chat-button:hover {
        transform: scale(1.05);
        background: #3d4a3d;
      }
      
      #hh-chat-button.hh-chat-button-closed {
        display: flex;
      }
      
      #hh-chat-button.hh-chat-button-open {
        display: none;
      }
      
      @media (max-width: 480px) {
        #hh-chat-widget {
          width: calc(100% - 40px);
          right: 20px;
          left: 20px;
        }
      }
    </style>
  `;

  // Inject widget
  document.head.insertAdjacentHTML('beforeend', widgetCSS);
  document.body.insertAdjacentHTML('beforeend', widgetHTML);

  // Chat functions
  window.hhChatToggle = function() {
    const widget = document.getElementById('hh-chat-widget');
    const button = document.getElementById('hh-chat-button');
    
    if (widget.classList.contains('hh-chat-closed')) {
      widget.classList.remove('hh-chat-closed');
      button.classList.remove('hh-chat-button-closed');
      button.classList.add('hh-chat-button-open');
      document.getElementById('hh-input').focus();
    } else {
      widget.classList.add('hh-chat-closed');
      button.classList.remove('hh-chat-button-open');
      button.classList.add('hh-chat-button-closed');
    }
  };

  window.hhChatSend = async function() {
    const input = document.getElementById('hh-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    hhAddMessage(message, 'user');
    input.value = '';
    
    // Send to Telegram via backend
    try {
      const response = await fetch('https://api.telegram.org/bot' + CONFIG.botToken + '/sendMessage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: CONFIG.chatId,
          text: `🏡 Hideaway 2200 Website Chat\\n\\n👤 Visitor: ${message}\\n\\nReply here to respond.`,
          parse_mode: 'Markdown'
        })
      });
      
      if (response.ok) {
        hhAddMessage('Message sent! The host will reply shortly.', 'bot');
      } else {
        hhAddMessage('Thanks for your message! We\'ll get back to you soon.', 'bot');
      }
    } catch (error) {
      console.error('Chat error:', error);
      // Fallback - could also email or store locally
      localStorage.setItem('hh-chat-pending', message);
      hhAddMessage('Thanks for your message! We\'ll get back to you soon.', 'bot');
    }
  };

  window.hhAddMessage = function(text, sender) {
    const container = document.getElementById('hh-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `hh-message hh-message-${sender}`;
    messageDiv.innerHTML = `
      <div class="hh-message-text">${hhEscapeHtml(text)}</div>
      <div class="hh-message-time">${hhFormatTime()}</div>
    `;
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
  };

  window.hhEscapeHtml = function(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  };

  // Auto-open chat after 30 seconds on first visit
  if (!localStorage.getItem('hh-chat-seen')) {
    setTimeout(() => {
      hhChatToggle();
      localStorage.setItem('hh-chat-seen', 'true');
    }, 30000);
  }
})();