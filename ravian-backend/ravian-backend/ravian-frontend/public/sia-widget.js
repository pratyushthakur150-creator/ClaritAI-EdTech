/**
 * ══════════════════════════════════════════════════════════════════════
 * SIA WIDGET v2.0 — SSSi Embeddable Chatbot
 * Drop-in script: <script src="/sia-widget.js" data-org="TENANT_UUID" data-api="https://..." data-color="#4F46E5"></script>
 * ══════════════════════════════════════════════════════════════════════
 */
(function () {
  "use strict";

  /* ── Configuration ─────────────────────────────────────────────── */
  const script = document.currentScript || document.querySelector("script[data-org]");
  const ORG_ID = (script && script.getAttribute("data-org")) || "";
  const API_BASE = (script && script.getAttribute("data-api")) || "";
  const PRIMARY_COLOR = (script && script.getAttribute("data-color")) || "#4F46E5";
  const BOT_NAME = (script && script.getAttribute("data-name")) || "Sia";
  const TYPING_MIN_MS = 800;
  const TYPING_MAX_MS = 1500;
  const INACTIVITY_TIMEOUT_MS = 60000; // 60s nudge
  const ATTENTION_PULSE_MS = 45000; // auto-pulse launcher
  const STORAGE_KEY = "sia_session_" + ORG_ID.slice(0, 8);

  if (!ORG_ID || !API_BASE) {
    console.warn("[Sia Widget] Missing data-org or data-api on script tag.");
    return;
  }

  /* ── Session State ─────────────────────────────────────────────── */
  let sessionState = {
    grade: null,
    board: null,
    subjects: [],
    goal: null,
    name: null,
    phone: null,
    user_type: null,
    preferred_time: null,
    language: "English",
    lead_captured: false,
  };
  let visitorId = null;
  let messages = [];
  let widgetOpen = false;
  let inactivityTimer = null;
  let pulseTimer = null;
  let isTyping = false;

  // Load persisted state
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      if (parsed.visitorId) visitorId = parsed.visitorId;
      if (parsed.sessionState) sessionState = { ...sessionState, ...parsed.sessionState };
      if (parsed.messages && parsed.messages.length) messages = parsed.messages;
    }
  } catch (e) { /* ignore */ }

  if (!visitorId) {
    visitorId = "sia_" + Math.random().toString(36).slice(2, 10) + "_" + Date.now();
  }

  function persistState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        visitorId,
        sessionState,
        messages: messages.slice(-30), // keep last 30 msgs
      }));
    } catch (e) { /* ignore */ }
  }

  /* ── Utilities ─────────────────────────────────────────────────── */
  function getTimeOfDay() {
    const h = new Date().getHours();
    if (h >= 6 && h < 12) return "morning";
    if (h >= 12 && h < 18) return "afternoon";
    if (h >= 18 && h < 23) return "evening";
    return "night";
  }

  function isHindi(text) {
    // Devanagari Unicode block: U+0900 to U+097F
    return /[\u0900-\u097F]/.test(text);
  }

  function isHinglish(text) {
    const hindiWords = ["kya", "hai", "kaise", "mujhe", "mera", "kitna", "haan", "nahi", "chahiye", "padhai", "padhna", "bhai", "yaar", "accha", "theek", "aur", "batao", "bata", "kab", "kahan", "kaun"];
    const lower = text.toLowerCase();
    return hindiWords.some(w => lower.includes(w));
  }

  function detectLanguage(text) {
    if (isHindi(text)) return "Hindi";
    if (isHinglish(text)) return "Hinglish";
    return "English";
  }

  function validatePhone(phone) {
    const digits = phone.replace(/[^0-9]/g, "");
    // Indian mobile: 10 digits starting with 6-9
    return /^[6-9]\d{9}$/.test(digits) || digits.length >= 10;
  }

  function randomDelay() {
    return TYPING_MIN_MS + Math.random() * (TYPING_MAX_MS - TYPING_MIN_MS);
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  /* ── Chip Parsing ──────────────────────────────────────────────── */
  // Parse [Button Text] and [🔍 Find a Tutor] patterns from bot responses
  function parseChips(text) {
    const chipRegex = /\[([^\[\]]{1,60})\]/g;
    const chips = [];
    let match;
    while ((match = chipRegex.exec(text)) !== null) {
      chips.push(match[1].trim());
    }
    // Remove chip patterns from display text
    const cleanText = text.replace(chipRegex, "").replace(/\s{2,}/g, " ").trim();
    return { cleanText, chips };
  }

  /* ── Format Bot Message (Bold, Bullets, Emoji) ─────────────────── */
  function formatBotHtml(text) {
    let html = escapeHtml(text);
    // Bold: **text**
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    // Italic: *text*
    html = html.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, "<em>$1</em>");
    // Newlines
    html = html.replace(/\n/g, "<br>");
    // ✅ / ❌ / 🔥 etc. — emojis render natively in modern browsers
    return html;
  }

  /* ── Inject Styles ─────────────────────────────────────────────── */
  function injectStyles() {
    if (document.getElementById("sia-widget-styles")) return;
    const style = document.createElement("style");
    style.id = "sia-widget-styles";
    style.textContent = `
      /* ── Sia Widget Container ── */
      #sia-widget-launcher {
        position: fixed; bottom: 24px; right: 24px; z-index: 99999;
        width: 60px; height: 60px; border-radius: 50%;
        background: ${PRIMARY_COLOR};
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; transition: transform 0.3s ease, box-shadow 0.3s ease;
        border: none; outline: none;
      }
      #sia-widget-launcher:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 28px rgba(0,0,0,0.35);
      }
      #sia-widget-launcher.pulse {
        animation: sia-pulse 1.5s ease-in-out infinite;
      }
      @keyframes sia-pulse {
        0%, 100% { box-shadow: 0 4px 20px rgba(0,0,0,0.25); }
        50% { box-shadow: 0 0 0 12px ${PRIMARY_COLOR}33, 0 4px 20px rgba(0,0,0,0.25); }
      }
      #sia-widget-launcher svg { width: 28px; height: 28px; fill: white; }

      /* ── Chat Window ── */
      #sia-widget-window {
        position: fixed; bottom: 96px; right: 24px; z-index: 99999;
        width: 380px; max-height: 560px; height: 560px;
        background: #ffffff; border-radius: 16px;
        box-shadow: 0 8px 40px rgba(0,0,0,0.18);
        display: none; flex-direction: column; overflow: hidden;
        font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
        animation: sia-slideUp 0.3s ease-out;
      }
      #sia-widget-window.open { display: flex; }
      @keyframes sia-slideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
      }

      /* ── Header ── */
      #sia-widget-header {
        background: ${PRIMARY_COLOR};
        padding: 16px 18px; display: flex; align-items: center; gap: 12px;
        color: white; flex-shrink: 0;
      }
      #sia-widget-avatar {
        width: 40px; height: 40px; border-radius: 50%;
        background: rgba(255,255,255,0.2); display: flex; align-items: center; justify-content: center;
        font-size: 20px; font-weight: 700; color: white; flex-shrink: 0;
      }
      #sia-widget-header-info h3 {
        margin: 0; font-size: 15px; font-weight: 600; line-height: 1.2;
      }
      #sia-widget-header-info p {
        margin: 2px 0 0; font-size: 12px; opacity: 0.85; line-height: 1.2;
      }
      #sia-widget-close {
        margin-left: auto; background: none; border: none; color: white;
        font-size: 22px; cursor: pointer; padding: 4px; line-height: 1;
        opacity: 0.8; transition: opacity 0.2s;
      }
      #sia-widget-close:hover { opacity: 1; }

      /* ── Messages Area ── */
      #sia-widget-messages {
        flex: 1; overflow-y: auto; padding: 16px;
        display: flex; flex-direction: column; gap: 10px;
        background: #f8f9fa;
      }
      #sia-widget-messages::-webkit-scrollbar { width: 4px; }
      #sia-widget-messages::-webkit-scrollbar-thumb { background: #ccc; border-radius: 4px; }

      .sia-msg { max-width: 85%; padding: 10px 14px; border-radius: 14px;
        font-size: 14px; line-height: 1.5; word-wrap: break-word;
        animation: sia-msgIn 0.25s ease-out; }
      @keyframes sia-msgIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .sia-msg.bot {
        align-self: flex-start; background: white; color: #1a1a1a;
        border-bottom-left-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
      }
      .sia-msg.user {
        align-self: flex-end; background: ${PRIMARY_COLOR}; color: white;
        border-bottom-right-radius: 4px;
      }

      /* ── Typing Indicator ── */
      .sia-typing { align-self: flex-start; display: flex; gap: 4px; padding: 12px 16px;
        background: white; border-radius: 14px; border-bottom-left-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
      .sia-typing-dot { width: 8px; height: 8px; border-radius: 50%; background: #bbb;
        animation: sia-bounce 1.4s ease-in-out infinite; }
      .sia-typing-dot:nth-child(2) { animation-delay: 0.2s; }
      .sia-typing-dot:nth-child(3) { animation-delay: 0.4s; }
      @keyframes sia-bounce {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-6px); }
      }

      /* ── Quick Reply Chips ── */
      .sia-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px;
        align-self: flex-start; max-width: 90%;
        animation: sia-msgIn 0.3s ease-out; }
      .sia-chip {
        background: white; border: 1.5px solid ${PRIMARY_COLOR}; color: ${PRIMARY_COLOR};
        padding: 7px 14px; border-radius: 20px; font-size: 13px; font-weight: 500;
        cursor: pointer; transition: all 0.2s ease; white-space: nowrap;
        font-family: inherit; line-height: 1.3;
      }
      .sia-chip:hover {
        background: ${PRIMARY_COLOR}; color: white;
        transform: translateY(-1px);
        box-shadow: 0 2px 8px ${PRIMARY_COLOR}44;
      }
      .sia-chip:active { transform: scale(0.96); }

      /* ── Input Area ── */
      #sia-widget-input-area {
        padding: 12px 14px; border-top: 1px solid #eee;
        display: flex; gap: 8px; align-items: center;
        background: white; flex-shrink: 0;
      }
      #sia-widget-input {
        flex: 1; border: 1px solid #ddd; border-radius: 24px;
        padding: 10px 16px; font-size: 14px; outline: none;
        font-family: inherit; transition: border-color 0.2s;
        background: #f8f9fa;
      }
      #sia-widget-input:focus { border-color: ${PRIMARY_COLOR}; background: white; }
      #sia-widget-input::placeholder { color: #999; }
      #sia-widget-send {
        width: 38px; height: 38px; border-radius: 50%; border: none;
        background: ${PRIMARY_COLOR}; color: white; cursor: pointer;
        display: flex; align-items: center; justify-content: center;
        transition: background 0.2s, transform 0.15s; flex-shrink: 0;
      }
      #sia-widget-send:hover { filter: brightness(1.1); transform: scale(1.05); }
      #sia-widget-send:active { transform: scale(0.95); }
      #sia-widget-send svg { width: 18px; height: 18px; fill: white; }

      /* ── Powered By ── */
      #sia-widget-powered {
        text-align: center; padding: 6px; font-size: 11px; color: #aaa;
        background: white; flex-shrink: 0;
      }
      #sia-widget-powered a { color: #888; text-decoration: none; }

      /* ── Mobile ── */
      @media (max-width: 480px) {
        #sia-widget-window {
          width: calc(100vw - 16px); right: 8px; bottom: 80px;
          max-height: calc(100vh - 100px); height: calc(100vh - 100px);
          border-radius: 12px;
        }
        #sia-widget-launcher { bottom: 16px; right: 16px; width: 54px; height: 54px; }
      }
    `;
    document.head.appendChild(style);
  }

  /* ── Build DOM ─────────────────────────────────────────────────── */
  function buildWidget() {
    // Launcher
    const launcher = document.createElement("button");
    launcher.id = "sia-widget-launcher";
    launcher.setAttribute("aria-label", "Chat with Sia");
    launcher.innerHTML = `<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/><path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg>`;
    launcher.onclick = toggleWidget;
    document.body.appendChild(launcher);

    // Chat window
    const win = document.createElement("div");
    win.id = "sia-widget-window";
    win.innerHTML = `
      <div id="sia-widget-header">
        <div id="sia-widget-avatar">S</div>
        <div id="sia-widget-header-info">
          <h3>${BOT_NAME} — SSSi Assistant</h3>
          <p>🟢 Online • Replies instantly</p>
        </div>
        <button id="sia-widget-close" aria-label="Close chat">&times;</button>
      </div>
      <div id="sia-widget-messages"></div>
      <div id="sia-widget-input-area">
        <input id="sia-widget-input" type="text" placeholder="Type your message..." autocomplete="off" maxlength="500">
        <button id="sia-widget-send" aria-label="Send message">
          <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
        </button>
      </div>
      <div id="sia-widget-powered">Powered by <a href="https://sssi.in" target="_blank" rel="noopener">SSSi.in</a></div>
    `;
    document.body.appendChild(win);

    // Events
    document.getElementById("sia-widget-close").onclick = toggleWidget;
    document.getElementById("sia-widget-send").onclick = () => handleSend();
    document.getElementById("sia-widget-input").addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
    });

    // Start attention pulse
    startPulse();
  }

  /* ── Toggle ────────────────────────────────────────────────────── */
  function toggleWidget() {
    widgetOpen = !widgetOpen;
    const win = document.getElementById("sia-widget-window");
    const launcher = document.getElementById("sia-widget-launcher");

    if (widgetOpen) {
      win.classList.add("open");
      launcher.classList.remove("pulse");
      stopPulse();

      // First open: show welcome or restore history
      if (messages.length === 0) {
        showWelcomeMessage();
      } else {
        renderAllMessages();
      }
      const input = document.getElementById("sia-widget-input");
      setTimeout(() => input && input.focus(), 300);
      resetInactivityTimer();
    } else {
      win.classList.remove("open");
      clearInactivityTimer();
    }
  }

  /* ── Welcome Message ───────────────────────────────────────────── */
  function showWelcomeMessage() {
    const tod = getTimeOfDay();
    const isReturn = sessionState.name || sessionState.grade;
    let greeting, chips;

    if (isReturn && sessionState.name) {
      greeting = `Welcome back, ${sessionState.name}! 😊 Ready to continue where we left off?`;
      chips = ["Resume Booking", "Start Fresh", "Talk to Counselor"];
    } else if (tod === "morning") {
      greeting = `🌅 Good morning! I'm ${BOT_NAME}, your SSSi learning assistant. Ready to find your perfect tutor? It takes under 30 seconds!`;
      chips = ["🔍 Find a Tutor", "📅 Book Free Trial", "💰 Pricing", "📞 Talk to Counselor"];
    } else if (tod === "afternoon") {
      greeting = `👋 Hi! I'm ${BOT_NAME}, your SSSi learning assistant. I can book a FREE demo class for you in under 30 seconds!`;
      chips = ["🔍 Find a Tutor", "📅 Book Free Trial", "💰 Pricing", "📞 Talk to Counselor"];
    } else if (tod === "evening" || tod === "night") {
      greeting = `🌙 Good evening! I'm ${BOT_NAME} from SSSi. Perfect time to plan your learning — want to book a free demo?`;
      chips = ["🔍 Find a Tutor", "📅 Book Free Trial", "💰 Pricing", "📞 Talk to Counselor"];
    } else {
      greeting = `👋 Hi! I'm ${BOT_NAME} from SSSi. How can I help you today?`;
      chips = ["🔍 Find a Tutor", "📅 Book Free Trial", "💰 Pricing"];
    }

    addBotMessage(greeting, chips);
  }

  /* ── Message Rendering ─────────────────────────────────────────── */
  function addBotMessage(text, chips) {
    messages.push({ role: "bot", text, chips: chips || [] });
    persistState();
    renderMessage({ role: "bot", text, chips: chips || [] });
    scrollToBottom();
  }

  function addUserMessage(text) {
    messages.push({ role: "user", text });
    persistState();
    renderMessage({ role: "user", text });
    scrollToBottom();
  }

  function renderMessage(msg) {
    const container = document.getElementById("sia-widget-messages");
    if (!container) return;

    if (msg.role === "user") {
      const div = document.createElement("div");
      div.className = "sia-msg user";
      div.textContent = msg.text;
      container.appendChild(div);
    } else {
      const div = document.createElement("div");
      div.className = "sia-msg bot";
      div.innerHTML = formatBotHtml(msg.text);
      container.appendChild(div);

      // Chips
      if (msg.chips && msg.chips.length > 0) {
        const chipContainer = document.createElement("div");
        chipContainer.className = "sia-chips";
        msg.chips.forEach(label => {
          const btn = document.createElement("button");
          btn.className = "sia-chip";
          btn.textContent = label;
          btn.onclick = () => handleChipClick(label);
          chipContainer.appendChild(btn);
        });
        container.appendChild(chipContainer);
      }
    }
  }

  function renderAllMessages() {
    const container = document.getElementById("sia-widget-messages");
    if (!container) return;
    container.innerHTML = "";
    messages.forEach(msg => renderMessage(msg));
    scrollToBottom();
  }

  function scrollToBottom() {
    const container = document.getElementById("sia-widget-messages");
    if (container) {
      setTimeout(() => { container.scrollTop = container.scrollHeight; }, 50);
    }
  }

  /* ── Typing Indicator ──────────────────────────────────────────── */
  function showTyping() {
    if (isTyping) return;
    isTyping = true;
    const container = document.getElementById("sia-widget-messages");
    if (!container) return;
    const typing = document.createElement("div");
    typing.className = "sia-typing";
    typing.id = "sia-typing-indicator";
    typing.innerHTML = `<div class="sia-typing-dot"></div><div class="sia-typing-dot"></div><div class="sia-typing-dot"></div>`;
    container.appendChild(typing);
    scrollToBottom();
  }

  function hideTyping() {
    isTyping = false;
    const el = document.getElementById("sia-typing-indicator");
    if (el) el.remove();
  }

  /* ── Chip Click Handler ────────────────────────────────────────── */
  function handleChipClick(label) {
    // Disable all chips after click (prevent double-click)
    document.querySelectorAll(".sia-chips").forEach(c => {
      const last = document.getElementById("sia-widget-messages").lastElementChild;
      if (c === last || c === last?.previousElementSibling) {
        c.querySelectorAll(".sia-chip").forEach(b => { b.disabled = true; b.style.opacity = "0.5"; b.style.cursor = "default"; });
      }
    });

    // Extract text for known chip actions
    const cleanLabel = label.replace(/^[^\w\s]+\s*/, "").trim(); // strip leading emojis
    handleSend(label);
  }

  /* ── Extract Session State from AI Response ────────────────────── */
  function extractStateFromResponse(botText, userText) {
    const lower = (userText || "").toLowerCase();

    // Grade detection from user's chip/text
    if (/class\s*1[\s\-–]5|class 1|class 2|class 3|class 4|class 5/i.test(lower)) sessionState.grade = "Class 1-5";
    else if (/class\s*6[\s\-–]8|class 6|class 7|class 8/i.test(lower)) sessionState.grade = "Class 6-8";
    else if (/class\s*9[\s\-–]10|class 9|class 10|10th/i.test(lower)) sessionState.grade = "Class 9-10";
    else if (/class\s*11[\s\-–]12|class 11|class 12|11th|12th/i.test(lower)) sessionState.grade = "Class 11-12";
    else if (/college|grad|undergraduate|postgrad/i.test(lower)) sessionState.grade = "College/Grad";
    else if (/professional|working/i.test(lower)) sessionState.grade = "Working Professional";

    // Board
    if (/\bcbse\b/i.test(lower)) sessionState.board = "CBSE";
    else if (/\bicse\b/i.test(lower)) sessionState.board = "ICSE";
    else if (/\bib\b/i.test(lower)) sessionState.board = "IB";
    else if (/\bigcse\b/i.test(lower)) sessionState.board = "IGCSE";
    else if (/\bcambridge\b/i.test(lower)) sessionState.board = "Cambridge";
    else if (/state\s*board/i.test(lower)) sessionState.board = "State Board";

    // Subjects (append, don't overwrite)
    const subjectMap = {
      maths: "Maths", math: "Maths", physics: "Physics", chemistry: "Chemistry",
      biology: "Biology", english: "English", hindi: "Hindi",
      "social studies": "Social Studies", "social science": "Social Science",
      computer: "Computer Science", accountancy: "Accountancy", economics: "Economics",
      "business studies": "Business Studies", coding: "Coding", "data science": "Data Science/AI",
      "digital marketing": "Digital Marketing", ai: "AI & ML",
    };
    Object.entries(subjectMap).forEach(([kw, name]) => {
      if (lower.includes(kw) && !sessionState.subjects.includes(name)) {
        sessionState.subjects.push(name);
      }
    });
    // "All Subjects" chip
    if (/all subjects/i.test(lower)) sessionState.subjects = ["All Subjects"];

    // Goal
    if (/jee/i.test(lower) && !sessionState.goal) sessionState.goal = "IIT-JEE";
    else if (/neet/i.test(lower) && !sessionState.goal) sessionState.goal = "NEET";
    else if (/olympiad/i.test(lower) && !sessionState.goal) sessionState.goal = "Olympiad";
    else if (/school exam|score better/i.test(lower) && !sessionState.goal) sessionState.goal = "School Exams";
    else if (/skill building|skill/i.test(lower) && !sessionState.goal) sessionState.goal = "Skill Building";
    else if (/general improvement/i.test(lower) && !sessionState.goal) sessionState.goal = "General Improvement";

    // User type (parent detection)
    if (/\b(my child|my son|my daughter|parent|my kid)\b/i.test(lower)) sessionState.user_type = "parent";

    // Name (from bot's confirmation echo)
    if (/demo booked|✅.*name:/i.test(botText)) {
      const nameMatch = botText.match(/👤\s*Name:\s*(.+?)[\n📚]/);
      if (nameMatch) sessionState.name = nameMatch[1].trim();
    }
    // Name from user typing (simple first-name extraction)
    if (!sessionState.name && /^[A-Z][a-z]{1,20}(\s+[A-Z][a-z]{1,20})?$/.test(userText.trim())) {
      // Only set if we're in the name-collection step (bot asked for name)
      const lastBot = messages.filter(m => m.role === "bot").slice(-1)[0];
      if (lastBot && /what('s| is) your name/i.test(lastBot.text)) {
        sessionState.name = userText.trim();
      }
    }

    // Phone
    const phoneMatch = lower.match(/(?:\+?91[\s-]?)?([6-9]\d{9})/);
    if (phoneMatch && !sessionState.phone) sessionState.phone = phoneMatch[1];

    // Preferred time
    if (/morning|8am|8\s*am/i.test(lower)) sessionState.preferred_time = "Morning 8AM-12PM";
    else if (/afternoon|12pm|12\s*pm|1pm|2pm|3pm/i.test(lower)) sessionState.preferred_time = "Afternoon 12PM-4PM";
    else if (/evening|4pm|5pm|6pm|7pm|8pm/i.test(lower)) sessionState.preferred_time = "Evening 4PM-8PM";

    // Language detection
    const lang = detectLanguage(userText);
    if (lang !== "English") sessionState.language = lang;

    persistState();
  }

  /* ── Auto Lead Capture ─────────────────────────────────────────── */
  function attemptLeadCapture() {
    if (sessionState.lead_captured) return;
    if (!sessionState.name || !sessionState.phone) return;

    sessionState.lead_captured = true;
    persistState();

    const payload = {
      tenant_id: ORG_ID,
      visitor_id: visitorId,
      name: sessionState.name,
      phone: sessionState.phone,
      grade: sessionState.grade,
      board: sessionState.board,
      subjects: sessionState.subjects,
      goal: sessionState.goal,
      user_type: sessionState.user_type,
      preferred_time: sessionState.preferred_time,
      language: sessionState.language,
    };

    fetch(API_BASE + "/api/v1/chatbot/capture-lead", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(r => r.json()).then(data => {
      console.log("[Sia] Lead captured:", data.lead_id, "temperature:", data.lead_temperature);
    }).catch(err => {
      console.warn("[Sia] Lead capture failed:", err);
      sessionState.lead_captured = false; // retry next time
      persistState();
    });
  }

  /* ── Send Message ──────────────────────────────────────────────── */
  async function handleSend(overrideText) {
    const input = document.getElementById("sia-widget-input");
    const text = (overrideText || (input && input.value) || "").trim();
    if (!text || isTyping) return;

    if (input) input.value = "";
    addUserMessage(text);

    // Extract state from what user typed
    extractStateFromResponse("", text);

    // Show typing
    showTyping();
    resetInactivityTimer();

    try {
      const payload = {
        tenant_id: ORG_ID,
        visitor_id: visitorId,
        message: text,
        session_state: sessionState,
      };

      const res = await fetch(API_BASE + "/api/v1/chatbot/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      const botResponse = data.response || data.message || "I'm having trouble — please try again!";

      // Simulate typing delay
      await new Promise(resolve => setTimeout(resolve, randomDelay()));
      hideTyping();

      // Parse chips from response
      const { cleanText, chips } = parseChips(botResponse);
      addBotMessage(cleanText || botResponse, chips);

      // Extract state from bot's response too
      extractStateFromResponse(botResponse, text);

      // Attempt auto lead capture if we have enough data
      attemptLeadCapture();

    } catch (err) {
      console.error("[Sia] API error:", err);
      hideTyping();
      addBotMessage("Oops — something went wrong! Please try again or reach us at sssi.in 📞", []);
    }
  }

  /* ── Inactivity Nudge ──────────────────────────────────────────── */
  function resetInactivityTimer() {
    clearInactivityTimer();
    inactivityTimer = setTimeout(() => {
      if (widgetOpen && !isTyping) {
        addBotMessage("Still there? No rush — just tap any option below when you're ready! 😊",
          ["📅 Book Free Demo", "💰 Pricing", "📞 Talk to Counselor"]);
      }
    }, INACTIVITY_TIMEOUT_MS);
  }

  function clearInactivityTimer() {
    if (inactivityTimer) { clearTimeout(inactivityTimer); inactivityTimer = null; }
  }

  /* ── Attention Pulse ───────────────────────────────────────────── */
  function startPulse() {
    if (widgetOpen) return;
    pulseTimer = setInterval(() => {
      const launcher = document.getElementById("sia-widget-launcher");
      if (launcher && !widgetOpen) {
        launcher.classList.add("pulse");
        setTimeout(() => launcher.classList.remove("pulse"), 3000);
      }
    }, ATTENTION_PULSE_MS);
  }

  function stopPulse() {
    if (pulseTimer) { clearInterval(pulseTimer); pulseTimer = null; }
  }

  /* ── Exit Intent Detection ─────────────────────────────────────── */
  function onMouseLeave(e) {
    if (e.clientY < 10 && !widgetOpen && messages.length === 0) {
      const launcher = document.getElementById("sia-widget-launcher");
      if (launcher) launcher.classList.add("pulse");
    }
  }
  document.addEventListener("mouseleave", onMouseLeave);

  /* ── Initialize ────────────────────────────────────────────────── */
  function init() {
    injectStyles();
    buildWidget();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
