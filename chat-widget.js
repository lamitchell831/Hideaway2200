// Hideaway 2200 Chat Widget
// Forwards messages to Telegram bot via Cloudflare Worker

(function() {
  // Configuration
  const CONFIG = {
    workerUrl: 'https://hideaway2200-chat.lamitchell831.workers.dev',
    welcomeMessage: 'Hi! Have questions about Hideaway 2200? Send us a message and we\'ll get back to you shortly.',
  };

  // Helper function for time
  function hhFormatTime() {
    return new Date().toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
  }

  // Create widget HTML
  const widgetHTML = `
    <div id="hh-chat-widget" class="hh-chat-closed">
      <div class="hh-chat-header">
        <span class="hh-chat-title">💬 Questions? Chat with Us</span>
        <button class="hh-chat-toggle" onclick="hhChatToggle()">−</button>
      </div>
      <div class="hh-chat-body">
        <div class="hh-chat-messages" id="hh-messages">
          <div class="hh-message hh-message-bot">
            <div class="hh-message-text">${CONFIG.welcomeMessage}</div>
            <div class="hh-message-time">${hhFormatTime()}</div>
          </div>
        </div>
        <div class="hh-chat-input-area-form">
          <input type="text" id="hh-name" placeholder="Your name" class="hh-input-field">
          <input type="email" id="hh-email" placeholder="Your email" class="hh-input-field">
          <textarea id="hh-message" placeholder="Your message..." class="hh-input-field hh-textarea" rows="3"></textarea>
          <button onclick="hhChatSend()" class="hh-send-btn">Send Message</button>
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
        width: 360px;
        height: 480px;
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
        flex: 0 0 auto;
        max-height: 140px;
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
      
      .hh-chat-input-area-form {
        flex: 1;
        padding: 16px;
        background: #fff;
        border-top: 1px solid #e8e6e1;
        display: flex;
        flex-direction: column;
        gap: 10px;
        overflow-y: auto;
      }
      
      .hh-input-field {
        padding: 12px 14px;
        border: 1px solid #d4d0c8;
        border-radius: 8px;
        font-size: 14px;
        font-family: inherit;
        outline: none;
        width: 100%;
        box-sizing: border-box;
      }
      
      .hh-input-field:focus {
        border-color: #2d3a2d;
      }
      
      .hh-textarea {
        resize: none;
        min-height: 80px;
      }
      
      .hh-send-btn {
        background: #2d3a2d;
        color: #f8f6f3;
        border: none;
        padding: 12px 20px;
        border-radius: 8px;
        font-size: 14px;
        cursor: pointer;
        font-weight: 500;
        transition: background 0.2s;
        margin-top: 4px;
      }
      
      .hh-send-btn:hover {
        background: #3d4a3d;
      }
      
      .hh-send-btn:disabled {
        background: #9a9a9a;
        cursor: not-allowed;
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
      
      #hh-chat-button.hh-chat-button-open {
        opacity: 0;
        pointer-events: none;
      }
      
      @media (max-width: 480px) {
        #hh-chat-widget {
          width: calc(100vw - 40px);
          right: 20px;
          left: 20px;
        }
      }
    </style>
  `;

  // Inject widget into page
  document.head.insertAdjacentHTML('beforeend', widgetCSS);
  document.body.insertAdjacentHTML('beforeend', widgetHTML);

  // Global functions
  window.hhChatToggle = function() {
    const widget = document.getElementById('hh-chat-widget');
    const button = document.getElementById('hh-chat-button');
    const isClosed = widget.classList.contains('hh-chat-closed');
    
    if (isClosed) {
      widget.classList.remove('hh-chat-closed');
      button.classList.add('hh-chat-button-open');
      document.querySelector('.hh-chat-toggle').textContent = '−';
    } else {
      widget.classList.add('hh-chat-closed');
      button.classList.remove('hh-chat-button-open');
      document.querySelector('.hh-chat-toggle').textContent = '+';
    }
  };

  window.hhChatSend = async function() {
    const nameInput = document.getElementById('hh-name');
    const emailInput = document.getElementById('hh-email');
    const messageInput = document.getElementById('hh-message');
    const sendBtn = document.querySelector('.hh-send-btn');
    
    const name = nameInput.value.trim();
    const email = emailInput.value.trim();
    const message = messageInput.value.trim();
    
    if (!message) {
      alert('Please enter a message.');
      return;
    }
    
    if (!email && !name) {
      alert('Please provide at least your name or email so we can respond.');
      return;
    }
    
    // Disable button while sending
    sendBtn.disabled = true;
    sendBtn.textContent = 'Sending...';
    
    try {
      const response = await fetch(CONFIG.workerUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, message })
      });
      
      const result = await response.json();
      
      if (result.success) {
        // Clear form
        nameInput.value = '';
        emailInput.value = '';
        messageInput.value = '';
        
        // Show success in chat
        const container = document.getElementById('hh-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'hh-message hh-message-bot';
        messageDiv.innerHTML = `
          <div class="hh-message-text">✓ Message sent! We'll get back to you within 24 hours.</div>
          <div class="hh-message-time">${hhFormatTime()}</div>
        `;
        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
        
        sendBtn.textContent = 'Sent!';
        setTimeout(() => {
          sendBtn.disabled = false;
          sendBtn.textContent = 'Send Message';
        }, 3000);
      } else {
        throw new Error(result.error || 'Failed to send');
      }
    } catch (error) {
      console.error('Chat error:', error);
      sendBtn.disabled = false;
      sendBtn.textContent = 'Send Message';
      alert('Having trouble sending. Please try again or email us directly.');
    }
  };

  window.hhFormatTime = hhFormatTime;

  // Auto-open chat after 30 seconds on first visit
  if (!localStorage.getItem('hh-chat-seen')) {
    setTimeout(() => {
      hhChatToggle();
      localStorage.setItem('hh-chat-seen', 'true');
    }, 30000);
  }
})();