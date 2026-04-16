/**
 * ClaritAI Chatbot Widget for SSSi Online Tutoring
 * Embed: <script src="https://ravian-backend-production.railway.app/static/sssi-chatbot.js" defer></script>
 */
(function () {
  "use strict";

  const CONFIG = {
    tenantId: "8a19c99f-3ebe-4c47-b483-b8796d122716",
    apiBaseUrl: "https://ravian-backend-production.railway.app",
    botName: "SSSI BOT",
    greeting:
      "Welcome to SSSi Online Tutoring — India's No.1 personalized online learning platform since 2015.\n\nI'm your AI assistant. I can help you with:\n\n• **Online Tuition:** Class 1 to 12 (CBSE, ICSE, State Boards)\n• **Competitive Exams:** IIT JEE, NEET, KVPY, NTSE, GATE\n• **Foreign Languages:** French, German, Spanish, Japanese & more\n• **Beyond Academics:** Abacus, Vedic Maths, Music, Robotics, AI\n• **Study Abroad Prep:** IELTS, PTE, TOEFL, GMAT, GRE prep\n\nHow can I help you today?",
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

    ._sssi-sugg-wrap { display:flex; flex-direction:column; gap:7px; margin-top:10px; align-items:flex-end; }
    ._sssi-sugg {
      background:#0062ff; color:#fff; border:none; border-radius:8px;
      padding:7px 14px; font-size:13px; cursor:pointer; font-family:inherit;
      font-weight:500; transition:background .2s;
    }
    ._sssi-sugg:hover { background:#004de8; }
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
            <div class="_sssi-name">${CONFIG.botName}</div>
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

  // ── Knowledge Base ─────────────────────────────────────────────────────────
  const KB = [
    {
      kw: ["hello","hi","hey","hii","namaste","good morning","good afternoon","good evening"],
      res: "Hello! Welcome to SSSi Online Tutoring.\n\nI'm here to help you find the perfect learning path. We offer personalized 1-on-1 online tuition for students from Class 1 to 12, competitive exam prep, foreign languages, and much more.\n\nWhat would you like to know?",
      sugg: ["What courses do you offer?", "Book a FREE trial class"]
    },
    {
      kw: ["course","courses","offer","subjects","program","tuition","class","classes","what do you"],
      res: "We offer a wide range of courses:\n\n• **Academic Tuition (Class 1-12):** All subjects across CBSE, ICSE, and State Boards.\n• **Competitive Exams:** IIT JEE, NEET, KVPY, NTSE, SSC, GATE.\n• **Foreign Languages:** French, German, Spanish, Chinese, Japanese, Turkish.\n• **Beyond Academics:** Abacus, Vedic Maths, Music, Robotics, AI, Python.\n• **Study Abroad Prep:** IELTS, PTE, TOEFL, GMAT, GRE.\n\nWould you like details on any specific course?",
      sugg: ["Pricing & fees", "How does it work?"]
    },
    {
      kw: ["price","pricing","fee","fees","cost","how much","payment","affordable","charge"],
      res: "Our fees are designed to be affordable and flexible:\n\n• **Personalized 1-on-1 classes:** Pricing varies by subject, class, and frequency.\n• **FREE trial class:** Available for every course — no commitment.\n• **Flexible payment plans:** Monthly packages available.\n• **Multi-subject discounts:** Bundle subjects to save more.\n\nFor an exact quote, book a free trial and our counselor will guide you.",
      sugg: ["Book a FREE trial class", "What courses do you offer?"]
    },
    {
      kw: ["trial","demo","book","enroll","register","sign up","free class","start"],
      res: "Yes, FREE trial class available!\n\nHere's what you'll experience:\n• Live 1-on-1 session with an expert tutor.\n• Interactive whiteboard for real-time learning.\n• Personalized attention to your learning style.\n\nTo book your slot, please share your details.",
      sugg: []
    },
    {
      kw: ["neet","jee","iit","medical","engineering","competitive"],
      res: "We provide comprehensive preparation for JEE and NEET:\n\n• **Subjects:** Physics, Chemistry, Biology, and Mathematics.\n• **Approach:** NCERT-focused with chapter-wise mock tests and PYQ practice.\n• **Guidance:** Expert 1-on-1 tutors to clear doubts instantly.\n\nStart your preparation with a free demo class!",
      sugg: ["Book a FREE trial class", "Pricing & fees"]
    },
    {
      kw: ["language","french","german","spanish","japanese","foreign","ielts","toefl","gmat","gre","pte"],
      res: "We offer expert coaching for foreign languages and study abroad tests:\n\n• **Languages:** French, German, Spanish, Chinese, Japanese, Turkish, Portuguese.\n• **Test Prep:** IELTS, PTE, TOEFL, GMAT, GRE — all levels.\n• **Experienced tutors** with proven track records.\n\nInterested? Book a FREE demo class today.",
      sugg: ["Book a FREE trial class"]
    },
    {
      kw: ["contact","call me","call","reach","speak","human","counselor","support"],
      res: "Our academic counselor will be happy to contact you!\n\nYou can also reach us directly:\n• **Phone/WhatsApp:** +91-742-867-2376\n• **Website:** www.sssi.in\n\nOr share your details and we'll call you back.",
      sugg: []
    },
    {
      kw: ["how does it work","how it works","how","process","platform","online"],
      res: "Here's how SSSi works:\n\n**Step 1:** Book a FREE trial class (no commitment).\n**Step 2:** Get matched with an expert tutor suited to your needs.\n**Step 3:** Learn live via our interactive online platform with HD video and a shared whiteboard.\n**Step 4:** Track your progress with regular assessments.\n\nAll sessions are recorded so you can revise anytime.",
      sugg: ["Book a FREE trial class", "Pricing & fees"]
    }
  ];

  // ── Lead Capture State Machine ─────────────────────────────────────────────
  let leadState = "none";
  let leadData = { name: "", email: "", phone: "" };

  function getResponse(userMsg) {
    const msg = userMsg.toLowerCase().trim();

    if (leadState === "asking_name") {
      leadData.name = userMsg.trim();
      leadState = "asking_email";
      return { res: `Thanks, **${leadData.name}**! What's your best **email address**?`, sugg: [] };
    }
    if (leadState === "asking_email") {
      if (!userMsg.includes("@") || !userMsg.includes(".")) {
        return { res: "That doesn't look like a valid email. Please enter a valid **email address**.", sugg: [] };
      }
      leadData.email = userMsg.trim();
      leadState = "asking_phone";
      return { res: "Got it! What's your **phone number** so our counselor can reach you?", sugg: [] };
    }
    if (leadState === "asking_phone") {
      const clean = userMsg.replace(/[^0-9+]/g, "");
      if (clean.length < 8) {
        return { res: "That phone number seems too short. Please enter a valid **phone number**.", sugg: [] };
      }
      leadData.phone = userMsg.trim();
      leadState = "none";
      submitLead(leadData);
      return {
        res: "Thank you! We've received your details.\n\nOur academic counselor will get in touch with you shortly.\n\nIs there anything else I can help you with?",
        sugg: ["What courses do you offer?", "Pricing & fees"]
      };
    }

    // Lead capture triggers
    const enrollKw = ["trial","demo","book","enroll","register","sign up","free class","start","call me","call","contact","human","counselor"];
    for (const kw of enrollKw) {
      if (msg.includes(kw)) {
        leadState = "asking_name";
        return {
          res: "I'd love to help you get started!\n\nCould you please share your **full name**?",
          sugg: []
        };
      }
    }

    // Detect email/phone shared directly
    const hasEmail = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/.test(msg);
    const hasPhone = /(?:\+?91[\s\-]?)?[6-9]\d{9}/.test(msg) || /\+?\d[\d\s\-()]{9,}/.test(msg);
    if (hasEmail || hasPhone) {
      return {
        res: "Thank you for sharing your contact details! Our counselor will reach out to you very soon.\n\nCan I help you with anything else?",
        sugg: ["What courses do you offer?"]
      };
    }

    // KB matching
    let best = null, bestScore = 0;
    for (const entry of KB) {
      let score = 0;
      for (const kw of entry.kw) {
        if (msg.includes(kw)) score += kw.length;
      }
      if (score > bestScore) { bestScore = score; best = entry; }
    }
    if (best && bestScore > 0) return { res: best.res, sugg: best.sugg || [] };

    return {
      res: "Thank you for reaching out!\n\nWe provide a comprehensive suite of learning solutions. Could you tell me a bit more about what you're looking for?",
      sugg: ["What courses do you offer?", "Book a FREE trial class"]
    };
  }

  // ── Submit Lead to Backend ─────────────────────────────────────────────────
  function submitLead(data) {
    const visitorId = getVisitorId();
    fetch(CONFIG.apiBaseUrl + "/api/v1/chatbot/capture-lead", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tenant_id: CONFIG.tenantId,
        visitor_id: visitorId,
        name: data.name,
        email: data.email,
        phone: data.phone,
        source_url: window.location.href
      })
    })
      .then(r => console.log("[SSSi ClaritAI] Lead sync:", r.ok ? "SUCCESS ✓" : "FAILED ✗", r.status))
      .catch(e => console.error("[SSSi ClaritAI] Lead sync error:", e));
  }

  function getVisitorId() {
    let vid = localStorage.getItem("_sssi_vid");
    if (!vid) {
      vid = "vid_" + Math.random().toString(36).substr(2, 12) + "_" + Date.now();
      localStorage.setItem("_sssi_vid", vid);
    }
    return vid;
  }

  // ── Markdown renderer ──────────────────────────────────────────────────────
  function renderMarkdown(text) {
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

  // ── DOM refs ───────────────────────────────────────────────────────────────
  const fab     = document.getElementById("_sssi-fab");
  const win     = document.getElementById("_sssi-win");
  const msgs    = document.getElementById("_sssi-msgs");
  const input   = document.getElementById("_sssi-input");
  const sendBtn = document.getElementById("_sssi-send");

  let isOpen = false, firstOpen = true, sending = false;

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
    if (firstOpen) { firstOpen = false; botMessage(CONFIG.greeting); }
  });

  document.getElementById("_sssi-close").addEventListener("click", () => {
    isOpen = false;
    win.classList.remove("open");
    fab.classList.remove("open");
  });

  document.getElementById("_sssi-refresh").addEventListener("click", () => {
    msgs.innerHTML = "";
    leadState = "none";
    leadData = { name: "", email: "", phone: "" };
    botMessage(CONFIG.greeting);
  });

  sendBtn.addEventListener("click", () => send(input.value));
  input.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input.value); }
  });

  // ── Messaging ──────────────────────────────────────────────────────────────
  async function botMessage(text, sugg = []) {
    const html = renderMarkdown(text);
    showTyping();
    await delay(650);
    hideTyping();

    const row = document.createElement("div");
    row.className = "_sssi-bot-row";
    row.innerHTML = `<div class="_sssi-bot-av">${BOT_SVG}</div><div class="_sssi-bot-text"></div>`;
    msgs.appendChild(row);
    await streamIn(html, row.querySelector("._sssi-bot-text"));

    if (sugg && sugg.length) renderSugg(sugg);
  }

  async function send(text) {
    if (!text || !text.trim() || sending) return;
    sending = true;
    input.value = "";
    sendBtn.classList.remove("on");
    sendBtn.disabled = true;

    document.querySelectorAll("._sssi-sugg-wrap").forEach(el => el.remove());

    const wrap = document.createElement("div");
    wrap.className = "_sssi-user-wrap";
    wrap.innerHTML = `
      <div class="_sssi-user-bubble">${text.replace(/</g,"&lt;").replace(/>/g,"&gt;")}</div>
      <div class="_sssi-read">Read</div>`;
    msgs.appendChild(wrap);
    scrollDown();

    const result = getResponse(text);
    await botMessage(result.res, result.sugg);
    sending = false;
  }

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
      await delay(18);
      spans[i].style.opacity = "1";
      scrollDown();
    }
  }

  function renderSugg(items) {
    const wrap = document.createElement("div");
    wrap.className = "_sssi-sugg-wrap";
    items.forEach(t => {
      const b = document.createElement("button");
      b.className = "_sssi-sugg";
      b.textContent = t;
      b.addEventListener("click", () => { b.style.opacity = "0.5"; b.style.pointerEvents = "none"; send(t); });
      wrap.appendChild(b);
    });
    msgs.appendChild(wrap);
    scrollDown();
  }

  function showTyping() {
    const row = document.createElement("div");
    row.className = "_sssi-typing-row";
    row.id = "_sssi-typing";
    row.innerHTML = `<div class="_sssi-bot-av">${BOT_SVG}</div><div class="_sssi-dots"><div class="_sssi-dot"></div><div class="_sssi-dot"></div><div class="_sssi-dot"></div></div>`;
    msgs.appendChild(row);
    scrollDown();
  }
  function hideTyping() { const t = document.getElementById("_sssi-typing"); if (t) t.remove(); }
  function scrollDown() { msgs.scrollTop = msgs.scrollHeight; }
  function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

})();
