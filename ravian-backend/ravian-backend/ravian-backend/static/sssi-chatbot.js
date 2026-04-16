/**
 * ClaritAI Chatbot Widget for SSSi Online Tutoring
 * Production RAG AI-powered widget — backed by GPT-4o-mini + ChromaDB
 * Embed: <script src="https://claritai-edtech-production.up.railway.app/static/sssi-chatbot.js" defer></script>
 */
(function () {
  "use strict";

  const CONFIG = {
    tenantId: "8a19c99f-3ebe-4c47-b483-b8796d122716",
    apiBaseUrl: "https://claritai-edtech-production.up.railway.app",
    botName: "SSSI BOT",
    greeting:
      "Welcome to SSSi Online Tutoring — India's No.1 personalized online learning platform since 2015.\n\nI'm your AI assistant. I can help you with:\n\n• **Online Tuition:** Class 1 to 12 (CBSE, ICSE, State Boards)\n• **Competitive Exams:** IIT JEE, NEET, KVPY, NTSE, GATE\n• **Foreign Languages:** French, German, Spanish, Japanese & more\n• **Beyond Academics:** Abacus, Vedic Maths, Robotics, Music, AI\n• **Study Abroad Prep:** IELTS, PTE, TOEFL, GMAT, GRE\n\nHow can I help you today?",
  };

  // ── Inject Styles ──────────────────────────────────────────────────────────
  const STYLES = `
    #_sssi-fab {
      position:fixed; bottom:28px; right:28px; width:60px; height:60px;
      border-radius:50%; border:none; cursor:pointer; z-index:2147483647;
      display:flex; align-items:center; justify-content:center;
      background:#0062ff; box-shadow:0 4px 16px rgba(0,98,255,0.4);
      transition:all .3s ease;
    }
    #_sssi-fab:hover { transform:scale(1.08); box-shadow:0 6px 22px rgba(0,98,255,0.5); }
    #_sssi-fab.open  { transform:scale(0.85) rotate(90deg); opacity:0; pointer-events:none; }
    #_sssi-fab svg   { width:26px; height:26px; fill:none; stroke:#fff; stroke-width:2.5; stroke-linecap:round; stroke-linejoin:round; }

    #_sssi-win {
      position:fixed; bottom:28px; right:28px;
      width:370px; max-width:calc(100vw - 24px);
      height:620px; max-height:calc(100vh - 56px);
      border-radius:14px; z-index:2147483646;
      display:none; flex-direction:column; overflow:hidden;
      font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
      background:#fcfcfc; border:1px solid #e8e8e8;
      box-shadow:0 12px 48px rgba(0,0,0,0.12);
    }
    #_sssi-win.open { display:flex; animation:_sssi_in .3s cubic-bezier(.16,1,.3,1); }
    @keyframes _sssi_in {
      from { opacity:0; transform:translateY(18px) scale(.97); }
      to   { opacity:1; transform:translateY(0)    scale(1); }
    }

    ._sssi-topbar {
      padding:14px 18px; display:flex; align-items:center;
      justify-content:space-between; background:#fff;
      border-bottom:1px solid #f0f0f0;
    }
    ._sssi-pill { display:flex; align-items:center; gap:10px; }
    ._sssi-av {
      width:32px; height:32px; border-radius:50%; background:#0062ff;
      display:flex; align-items:center; justify-content:center; flex-shrink:0;
    }
    ._sssi-name { font-size:15px; font-weight:600; color:#1e293b; }
    ._sssi-status { font-size:11px; color:#22c55e; margin-top:1px; }
    ._sssi-ai-badge {
      font-size:10px; background:#eef2ff; color:#4f46e5; padding:2px 7px;
      border-radius:10px; font-weight:600; margin-left:4px; letter-spacing:.3px;
    }
    ._sssi-topicons { display:flex; gap:10px; align-items:center; }
    ._sssi-tbtn {
      background:#f1f5f9; border:none; cursor:pointer;
      width:28px; height:28px; border-radius:50%;
      display:flex; align-items:center; justify-content:center;
      transition:background .2s;
    }
    ._sssi-tbtn:hover { background:#e2e8f0; }

    ._sssi-msgs {
      flex:1; padding:18px; background:#fcfcfc;
      display:flex; flex-direction:column; gap:14px;
      overflow-y:auto; scroll-behavior:smooth;
    }
    ._sssi-msgs::-webkit-scrollbar { width:5px; }
    ._sssi-msgs::-webkit-scrollbar-thumb { background:#cbd5e1; border-radius:10px; }

    ._sssi-bot-row { display:flex; gap:10px; align-items:flex-start; margin-bottom:4px; }
    ._sssi-bot-av  {
      width:26px; height:26px; border-radius:50%; background:#0062ff;
      display:flex; align-items:center; justify-content:center; flex-shrink:0; margin-top:2px;
    }
    ._sssi-bot-text { font-size:14px; color:#334155; line-height:1.65; max-width:270px; }
    ._sssi-bot-text p  { margin-bottom:6px; }
    ._sssi-bot-text ul { margin:6px 0; padding-left:18px; }
    ._sssi-bot-text li { margin-bottom:4px; }
    ._sssi-bot-text strong { font-weight:600; }

    ._sssi-user-wrap { display:flex; flex-direction:column; align-items:flex-end; gap:3px; margin-bottom:4px; }
    ._sssi-user-bubble {
      background:#0062ff; border-radius:16px 16px 4px 16px;
      padding:9px 14px; font-size:14px; color:#fff;
      max-width:250px; word-break:break-word; line-height:1.5;
    }
    ._sssi-read { font-size:11px; color:#94a3b8; padding-right:2px; }

    ._sssi-typing-row { display:flex; gap:10px; align-items:flex-start; margin-bottom:4px; }
    ._sssi-dots { display:flex; gap:4px; padding:8px 0; }
    ._sssi-dot  { width:6px; height:6px; border-radius:50%; background:#94a3b8; animation:_sssi_bounce 1.4s ease-in-out infinite; }
    ._sssi-dot:nth-child(1) { animation-delay:-.32s; }
    ._sssi-dot:nth-child(2) { animation-delay:-.16s; }
    @keyframes _sssi_bounce {
      0%,80%,100% { transform:scale(.6); opacity:.4; }
      40%          { transform:scale(1);  opacity:1;   }
    }

    ._sssi-inputbar { padding:10px 18px; background:#fff; border-top:1px solid #f0f0f0; }
    ._sssi-inputinner {
      display:flex; align-items:center; gap:8px; background:#fff;
      border-radius:22px; padding:7px 10px 7px 14px; border:1px solid #e2e8f0;
      transition:border-color .2s;
    }
    ._sssi-inputinner:focus-within { border-color:#0062ff; box-shadow:0 0 0 3px rgba(0,98,255,.08); }
    ._sssi-inputinner input {
      flex:1; border:none; outline:none; font-size:14px; color:#334155;
      background:transparent; min-width:0; font-family:inherit;
    }
    ._sssi-inputinner input::placeholder { color:#94a3b8; }
    ._sssi-inputinner input:disabled { opacity:0.5; }
    ._sssi-sendbtn {
      width:32px; height:32px; background:#e2e8f0; border-radius:50%;
      display:flex; align-items:center; justify-content:center;
      cursor:pointer; border:none; transition:all .2s; flex-shrink:0;
    }
    ._sssi-sendbtn.on { background:#0062ff; }
    ._sssi-sendbtn svg { width:14px; height:14px; fill:#94a3b8; transition:fill .2s; }
    ._sssi-sendbtn.on svg { fill:#fff; }

    ._sssi-footer { padding:0 18px 12px; text-align:center; background:#fff; }
    ._sssi-footer span   { font-size:11px; color:#94a3b8; }
    ._sssi-footer strong { font-size:11px; color:#0f172a; font-weight:600; }

    ._sssi-err { font-size:12px; color:#ef4444; padding:6px 10px; background:#fef2f2; border-radius:8px; margin-bottom:4px; }
  `;

  // ── Inject font + styles ───────────────────────────────────────────────────
  (function injectFont() {
    if (!document.querySelector('link[href*="fonts.googleapis.com/css2?family=Inter"]')) {
      const l = document.createElement("link");
      l.rel = "stylesheet";
      l.href = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap";
      document.head.appendChild(l);
    }
  })();

  const styleEl = document.createElement("style");
  styleEl.textContent = STYLES;
  document.head.appendChild(styleEl);

  // ── Build HTML ─────────────────────────────────────────────────────────────
  const BOT_SVG = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M12 2L14.5 9.5L22 12L14.5 14.5L12 22L9.5 14.5L2 12L9.5 9.5L12 2Z" fill="#fff"/></svg>`;

  const wrapper = document.createElement("div");
  wrapper.innerHTML = `
    <button id="_sssi-fab" aria-label="Chat with SSSi">
      <svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
    </button>

    <div id="_sssi-win" role="dialog" aria-label="SSSi Chatbot">
      <div class="_sssi-topbar">
        <div class="_sssi-pill">
          <div class="_sssi-av">${BOT_SVG}</div>
          <div>
            <div class="_sssi-name">${CONFIG.botName} <span class="_sssi-ai-badge">AI</span></div>
            <div class="_sssi-status">● Online</div>
          </div>
        </div>
        <div class="_sssi-topicons">
          <button class="_sssi-tbtn" id="_sssi-refresh" title="Restart chat">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M1 4v6h6M23 20v-6h-6" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <button class="_sssi-tbtn" id="_sssi-close" title="Close">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M18 6L6 18M6 6l12 12" stroke="#64748b" stroke-width="2" stroke-linecap="round"/></svg>
          </button>
        </div>
      </div>

      <div class="_sssi-msgs" id="_sssi-msgs"></div>

      <div class="_sssi-inputbar">
        <div class="_sssi-inputinner">
          <input type="text" id="_sssi-input" placeholder="Type a message..." autocomplete="off" />
          <button class="_sssi-sendbtn" id="_sssi-send" disabled>
            <svg viewBox="0 0 24 24"><path d="M12 19V5M12 5L5 12M12 5L19 12" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
        </div>
      </div>

      <div class="_sssi-footer">
        <span>Powered by </span><strong>ClaritAI</strong>
      </div>
    </div>
  `;
  document.body.appendChild(wrapper);

  // ── State ──────────────────────────────────────────────────────────────────
  let visitorId = getVisitorId();
  let isOpen = false, firstOpen = true, sending = false;

  // ── DOM refs ───────────────────────────────────────────────────────────────
  const fab     = document.getElementById("_sssi-fab");
  const win     = document.getElementById("_sssi-win");
  const msgs    = document.getElementById("_sssi-msgs");
  const input   = document.getElementById("_sssi-input");
  const sendBtn = document.getElementById("_sssi-send");

  // ── Event Listeners ────────────────────────────────────────────────────────
  input.addEventListener("input", () => {
    const hasText = input.value.trim().length > 0;
    sendBtn.classList.toggle("on", hasText);
    sendBtn.disabled = !hasText;
  });

  fab.addEventListener("click", () => {
    isOpen = true;
    win.classList.add("open");
    fab.classList.add("open");
    input.focus();
    if (firstOpen) { firstOpen = false; showGreeting(); }
  });

  document.getElementById("_sssi-close").addEventListener("click", () => {
    isOpen = false;
    win.classList.remove("open");
    fab.classList.remove("open");
  });

  document.getElementById("_sssi-refresh").addEventListener("click", () => {
    msgs.innerHTML = "";
    visitorId = "vid_" + Math.random().toString(36).substr(2, 12) + "_" + Date.now();
    localStorage.setItem("_sssi_vid", visitorId);
    showGreeting();
  });

  sendBtn.addEventListener("click", () => send(input.value));
  input.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input.value); }
  });

  // ── Greeting (local, no API call) ──────────────────────────────────────────
  function showGreeting() {
    botMessage(CONFIG.greeting, false); // false = no stream, instant render
  }

  // ── Call AI Backend ────────────────────────────────────────────────────────
  async function callAI(userMessage) {
    const response = await fetch(CONFIG.apiBaseUrl + "/api/v1/chatbot/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tenant_id: CONFIG.tenantId,
        visitor_id: visitorId,
        message: userMessage,
      }),
    });

    if (!response.ok) {
      throw new Error("API error " + response.status);
    }

    const data = await response.json();
    return data.response || "I'm sorry, I didn't understand that. Could you rephrase?";
  }

  // ── Send message ───────────────────────────────────────────────────────────
  async function send(text) {
    if (!text || !text.trim() || sending) return;
    sending = true;
    input.value = "";
    input.disabled = true;
    sendBtn.classList.remove("on");
    sendBtn.disabled = true;

    // User bubble
    const wrap = document.createElement("div");
    wrap.className = "_sssi-user-wrap";
    wrap.innerHTML = `
      <div class="_sssi-user-bubble">${text.replace(/</g,"&lt;").replace(/>/g,"&gt;")}</div>
      <div class="_sssi-read">Read</div>`;
    msgs.appendChild(wrap);
    scrollDown();

    // Show typing indicator
    showTyping();

    try {
      const aiText = await callAI(text);
      hideTyping();
      await botMessage(aiText, true); // true = stream words
    } catch (err) {
      hideTyping();
      console.error("[SSSi AI] Error:", err);
      // Graceful fallback message
      await botMessage(
        "I'm having trouble connecting right now. Please call us directly at **+91-742-867-2376** or visit **www.sssi.in** — our counselors are available 8 AM to 10 PM daily.",
        true
      );
    } finally {
      sending = false;
      input.disabled = false;
      input.focus();
    }
  }

  // ── Render bot message ─────────────────────────────────────────────────────
  async function botMessage(text, stream = true) {
    const html = renderMarkdown(text);

    if (!stream) {
      const row = document.createElement("div");
      row.className = "_sssi-bot-row";
      row.innerHTML = `<div class="_sssi-bot-av">${BOT_SVG}</div><div class="_sssi-bot-text">${html}</div>`;
      msgs.appendChild(row);
      scrollDown();
      return;
    }

    const row = document.createElement("div");
    row.className = "_sssi-bot-row";
    row.innerHTML = `<div class="_sssi-bot-av">${BOT_SVG}</div><div class="_sssi-bot-text"></div>`;
    msgs.appendChild(row);
    await streamIn(html, row.querySelector("._sssi-bot-text"));
  }

  // ── Markdown renderer ──────────────────────────────────────────────────────
  function renderMarkdown(text) {
    if (!text) return "";
    const lines = text.split("\n");
    let html = "", inList = false;
    for (const rawLine of lines) {
      let line = rawLine.trim();
      if (!line) { if (inList) { html += "</ul>"; inList = false; } continue; }
      line = line.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
      if (line.startsWith("•") || line.startsWith("-") || /^\*\s/.test(line)) {
        if (!inList) { html += `<ul>`; inList = true; }
        html += `<li>${line.replace(/^[•\-\*]\s*/, "")}</li>`;
      } else {
        if (inList) { html += "</ul>"; inList = false; }
        html += `<p>${line}</p>`;
      }
    }
    if (inList) html += "</ul>";
    return html;
  }

  // ── Word streaming ─────────────────────────────────────────────────────────
  async function streamIn(htmlStr, container) {
    container.innerHTML = htmlStr;
    const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, null, false);
    const nodes = [];
    let n;
    while ((n = walker.nextNode())) { if (n.nodeValue.trim()) nodes.push(n); }

    nodes.forEach(node => {
      const words = node.nodeValue.split(/(\s+)/);
      const frag = document.createDocumentFragment();
      words.forEach(w => {
        if (w.trim()) {
          const s = document.createElement("span");
          s.textContent = w;
          s.style.cssText = "opacity:0;transition:opacity .12s ease-out";
          s.className = "_sw";
          frag.appendChild(s);
        } else {
          frag.appendChild(document.createTextNode(w));
        }
      });
      node.parentNode.replaceChild(frag, node);
    });

    const spans = container.querySelectorAll("._sw");
    for (let i = 0; i < spans.length; i++) {
      await delay(16);
      spans[i].style.opacity = "1";
      if (i % 5 === 0) scrollDown();
    }
    scrollDown();
  }

  // ── Typing indicator ───────────────────────────────────────────────────────
  function showTyping() {
    const row = document.createElement("div");
    row.className = "_sssi-typing-row";
    row.id = "_sssi-typing";
    row.innerHTML = `<div class="_sssi-bot-av">${BOT_SVG}</div><div class="_sssi-dots"><div class="_sssi-dot"></div><div class="_sssi-dot"></div><div class="_sssi-dot"></div></div>`;
    msgs.appendChild(row);
    scrollDown();
  }
  function hideTyping() { const t = document.getElementById("_sssi-typing"); if (t) t.remove(); }

  // ── Helpers ────────────────────────────────────────────────────────────────
  function scrollDown() { msgs.scrollTop = msgs.scrollHeight; }
  function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

  function getVisitorId() {
    let vid = localStorage.getItem("_sssi_vid");
    if (!vid) {
      vid = "vid_" + Math.random().toString(36).substr(2, 12) + "_" + Date.now();
      localStorage.setItem("_sssi_vid", vid);
    }
    return vid;
  }

})();
