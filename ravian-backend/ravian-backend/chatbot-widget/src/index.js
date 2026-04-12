const EdTechChatbot = {
  _config: null,
  _initialized: false,

  init(config) {
    if (this._initialized) return;
    this._initialized = true;

    this._config = {
      apiBaseUrl: config.apiBaseUrl || 'http://127.0.0.1:8001',
      tenantId: config.tenantId || '',
      apiKey: config.apiKey || '',
      theme: {
        primaryColor: config.theme?.primaryColor || '#4F46E5',
        position: config.theme?.position || 'bottom-right',
        greeting: config.theme?.greeting || 'Hi! How can I help you today?',
      },
    };

    // Persist a visitor/session ID in localStorage so that
    // chatbot sessions can be correlated with leads in the CRM.
    try {
      if (typeof window !== 'undefined') {
        const storageKey = '_clariai_visitor_id';
        let visitorId = window.localStorage.getItem(storageKey);
        if (!visitorId) {
          visitorId = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
          window.localStorage.setItem(storageKey, visitorId);
        }
        this._config.visitorId = visitorId;
      }
    } catch {
      // Fallback to runtime-generated ID only
      this._config.visitorId = null;
    }

    this._inject();
    console.log('[ClariAI] Chatbot initialized');
  },

  _inject() {
    const c = this._config;
    const isLeft = c.theme.position === 'bottom-left';
    const pos = isLeft ? 'bottom:20px;left:20px;' : 'bottom:20px;right:20px;';
    const winPos = isLeft ? 'bottom:90px;left:20px;' : 'bottom:90px;right:20px;';

    const style = document.createElement('style');
    style.textContent = `
      #_clari-btn{position:fixed;${pos}width:60px;height:60px;border-radius:50%;
        background:${c.theme.primaryColor};border:none;cursor:pointer;z-index:2147483647;
        box-shadow:0 4px 20px rgba(0,0,0,0.28);display:flex;align-items:center;
        justify-content:center;transition:transform .2s;}
      #_clari-btn:hover{transform:scale(1.08);}
      #_clari-win{position:fixed;${winPos}width:360px;height:520px;background:#fff;
        border-radius:16px;box-shadow:0 16px 56px rgba(0,0,0,0.2);z-index:2147483646;
        display:none;flex-direction:column;overflow:hidden;font-family:-apple-system,sans-serif;}
      #_clari-win.open{display:flex;animation:_clariUp .25s ease;}
      @keyframes _clariUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
      #_clari-hdr{background:${c.theme.primaryColor};color:#fff;padding:16px 18px;
        display:flex;justify-content:space-between;align-items:center;}
      #_clari-hdr h3{margin:0;font-size:15px;font-weight:600;}
      #_clari-x{background:none;border:none;color:#fff;font-size:22px;cursor:pointer;padding:0;}
      #_clari-msgs{flex:1;overflow-y:auto;padding:14px;background:#f8f9fa;font-size:14px;}
      ._cm{margin-bottom:10px;display:flex;flex-direction:column;}
      ._cm.u{align-items:flex-end;}._cm.b{align-items:flex-start;}
      ._cb{padding:9px 13px;border-radius:12px;max-width:82%;word-break:break-word;line-height:1.45;}
      ._cm.u ._cb{background:${c.theme.primaryColor};color:#fff;}
      ._cm.b ._cb{background:#fff;color:#1f2937;border:1px solid #e5e7eb;}
      ._ct{display:flex;gap:4px;padding:9px 13px;}
      ._cd{width:8px;height:8px;border-radius:50%;background:#9ca3af;animation:_dots 1.4s infinite ease-in-out;}
      ._cd:nth-child(1){animation-delay:-.32s}._cd:nth-child(2){animation-delay:-.16s}
      @keyframes _dots{0%,80%,100%{transform:scale(0)}40%{transform:scale(1)}}
      #_clari-inp-row{display:flex;gap:8px;padding:12px;background:#fff;border-top:1px solid #e5e7eb;}
      #_clari-inp{flex:1;padding:9px 12px;border:1px solid #d1d5db;border-radius:10px;
        font-size:14px;outline:none;font-family:inherit;}
      #_clari-inp:focus{border-color:${c.theme.primaryColor};}
      #_clari-snd{background:${c.theme.primaryColor};color:#fff;border:none;border-radius:10px;
        padding:9px 14px;cursor:pointer;font-size:14px;}
    `;
    document.head.appendChild(style);

    const btn = document.createElement('button');
    btn.id = '_clari-btn';
    btn.innerHTML = `<svg width="26" height="26" fill="none" stroke="#fff" stroke-width="2.2" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`;
    document.body.appendChild(btn);

    const win = document.createElement('div');
    win.id = '_clari-win';
    win.innerHTML = `
      <div id="_clari-hdr">
        <h3>💬 ClariAI Assistant</h3>
        <button id="_clari-x">✕</button>
      </div>
      <div id="_clari-msgs"></div>
      <div id="_clari-inp-row">
        <input id="_clari-inp" placeholder="Type your message..." />
        <button id="_clari-snd">Send</button>
      </div>`;
    document.body.appendChild(win);

    const msgs = document.getElementById('_clari-msgs');
    const inp = document.getElementById('_clari-inp');

    this._addMsg('b', c.theme.greeting);

    btn.onclick = () => win.classList.toggle('open');
    document.getElementById('_clari-x').onclick = () => win.classList.remove('open');

    const send = async () => {
      const text = inp.value.trim();
      if (!text) return;
      inp.value = '';
      this._addMsg('u', text);

      // Simple pattern: "Name, email, course" to help
      // the backend reliably capture leads from one line.
      const leadPattern = /^(.+?),\s*(.+?@.+?),\s*(.+?)$/;
      const leadMatch = leadPattern.exec(text);

      this._showTyping();
      try {
        const payload = {
          message: text,
          tenant_id: c.tenantId,
        };
        if (this._config.visitorId) {
          payload.visitor_id = this._config.visitorId;
        }

        const res = await fetch(`${c.apiBaseUrl}/api/v1/chatbot/message`, {
          method: 'POST',
          mode: 'cors',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        this._hideTyping();
        const data = await res.json();

        // If backend indicates lead captured, reinforce confirmation message.
        if (data.lead_captured && leadMatch) {
          const [, name, , course] = leadMatch;
          this._addMsg(
            'b',
            `Thank you, ${name}! I've captured your details for ${course}. Our team will contact you shortly.`
          );
        } else {
          this._addMsg(
            'b',
            data.response || data.message || 'Thank you! Our team will contact you soon.'
          );
        }
      } catch (e) {
        console.error('Chat error:', e);
        this._hideTyping();
        this._addMsg('b', 'Thanks for reaching out! Our counselors will contact you shortly.');
      }
    };

    document.getElementById('_clari-snd').onclick = send;
    inp.onkeydown = e => { if (e.key === 'Enter') send(); };
  },

  _addMsg(role, text) {
    const msgs = document.getElementById('_clari-msgs');
    if (!msgs) return;
    const d = document.createElement('div');
    d.className = `_cm ${role}`;
    d.innerHTML = `<div class="_cb">${text}</div>`;
    msgs.appendChild(d);
    msgs.scrollTop = msgs.scrollHeight;
  },

  _showTyping() {
    const msgs = document.getElementById('_clari-msgs');
    if (!msgs) return;
    const t = document.createElement('div');
    t.id = '_clari-typing';
    t.className = '_cm b';
    t.innerHTML = `<div class="_cb _ct"><div class="_cd"></div><div class="_cd"></div><div class="_cd"></div></div>`;
    msgs.appendChild(t);
    msgs.scrollTop = msgs.scrollHeight;
  },

  _hideTyping() {
    const t = document.getElementById('_clari-typing');
    if (t) t.remove();
  },
};

if (typeof window !== 'undefined') {
  window.EdTechChatbot = EdTechChatbot;
  window.ClariChatbot = EdTechChatbot;
}

export default EdTechChatbot;
