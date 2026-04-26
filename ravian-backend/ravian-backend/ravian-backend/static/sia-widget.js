/**
 * ══════════════════════════════════════════════════════════════════════
 * SIA WIDGET v3.0 — SSSi Embeddable Chatbot (Premium Edition)
 * Drop-in script: <script src="/sia-widget.js" data-org="TENANT_UUID" data-api="https://..." data-color="#d11c5d"></script>
 * ══════════════════════════════════════════════════════════════════════
 */
(function () {
  "use strict";

  /* ── Configuration ─────────────────────────────────────────────── */
  const script = document.currentScript || document.querySelector("script[data-org]");
  const ORG_ID = (script && script.getAttribute("data-org")) || "";
  const API_BASE = (script && script.getAttribute("data-api")) || "";
  const PRIMARY_COLOR = (script && script.getAttribute("data-color")) || "#d11c5d";
  const SECONDARY_COLOR = (script && script.getAttribute("data-secondary")) || "#7d3384";
  const BOT_NAME = (script && script.getAttribute("data-name")) || "Sia";
  const TYPING_MIN_MS = 800;
  const TYPING_MAX_MS = 1500;
  const TYPEWRITER_CHAR_MS = 18; // ms per character for typewriter
  const INACTIVITY_TIMEOUT_MS = 60000;
  const ATTENTION_PULSE_MS = 45000;
  const STORAGE_KEY = "sia_session_" + ORG_ID.slice(0, 8);

  if (!ORG_ID || !API_BASE) {
    console.warn("[Sia Widget] Missing data-org or data-api on script tag.");
    return;
  }

  /* ── Load Google Font ─────────────────────────────────────────── */
  if (!document.querySelector('link[href*="Inter"]')) {
    const fontLink = document.createElement("link");
    fontLink.href = "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap";
    fontLink.rel = "stylesheet";
    document.head.appendChild(fontLink);
  }

  /* ── Session State ─────────────────────────────────────────────── */
  let sessionState = {
    grade: null, board: null, subjects: [], goal: null,
    name: null, phone: null, email: null, user_type: null,
    preferred_time: null, language: "English", lead_captured: false,
  };
  let visitorId = null;
  let messages = [];
  let widgetOpen = false;
  let inactivityTimer = null;
  let pulseTimer = null;
  let isTyping = false;
  let isTypewriting = false;

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
        visitorId, sessionState,
        messages: messages.slice(-30),
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
  function parseChips(text) {
    const chipRegex = /\[([^\[\]]{1,60})\]/g;
    const chips = [];
    let match;
    while ((match = chipRegex.exec(text)) !== null) {
      chips.push(match[1].trim());
    }
    const cleanText = text.replace(chipRegex, "").replace(/\s{2,}/g, " ").trim();
    return { cleanText, chips };
  }

  /* ── Format Bot Message (Bold, Bullets, Emoji) ─────────────────── */
  function formatBotHtml(text) {
    let html = escapeHtml(text);
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, "<em>$1</em>");
    html = html.replace(/\n/g, "<br>");
    return html;
  }

  /* ── Inject Styles ─────────────────────────────────────────────── */
  function injectStyles() {
    if (document.getElementById("sia-widget-styles")) return;
    const style = document.createElement("style");
    style.id = "sia-widget-styles";
    style.textContent = `
      /* ── CSS Custom Properties ── */
      :root {
        --sia-primary: ${PRIMARY_COLOR};
        --sia-secondary: ${SECONDARY_COLOR};
        --sia-gradient: linear-gradient(135deg, ${PRIMARY_COLOR} 0%, ${SECONDARY_COLOR} 100%);
        --sia-gradient-hover: linear-gradient(135deg, ${SECONDARY_COLOR} 0%, ${PRIMARY_COLOR} 100%);
        --sia-bg-dark: #1a1a2e;
        --sia-bg-card: #16213e;
        --sia-bg-msg: #0f3460;
        --sia-text-primary: #f0f0f0;
        --sia-text-secondary: #a0a0c0;
        --sia-glass: rgba(255,255,255,0.06);
        --sia-glass-border: rgba(255,255,255,0.12);
        --sia-font: 'Inter', system-ui, -apple-system, sans-serif;
        --sia-radius: 16px;
        --sia-shadow: 0 20px 60px rgba(0,0,0,0.4), 0 0 40px rgba(209,28,93,0.15);
        --sia-shadow-launcher: 0 8px 32px rgba(209,28,93,0.4), 0 4px 16px rgba(0,0,0,0.3);
      }

      /* ── Launcher Button ── */
      #sia-widget-launcher {
        position: fixed; bottom: 28px; right: 28px; z-index: 99999;
        width: 64px; height: 64px; border-radius: 50%;
        background: var(--sia-gradient);
        box-shadow: var(--sia-shadow-launcher);
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; border: none; outline: none;
        transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        overflow: hidden;
      }
      #sia-widget-launcher::before {
        content: '';
        position: absolute;
        inset: 0;
        border-radius: 50%;
        background: var(--sia-gradient-hover);
        opacity: 0;
        transition: opacity 0.3s ease;
      }
      #sia-widget-launcher:hover::before { opacity: 1; }
      #sia-widget-launcher:hover {
        transform: scale(1.12) rotate(5deg);
        box-shadow: 0 12px 40px rgba(209,28,93,0.5), 0 0 60px rgba(125,51,132,0.3);
      }
      #sia-widget-launcher:active {
        transform: scale(0.92);
      }

      /* Launcher ripple ring */
      #sia-widget-launcher::after {
        content: '';
        position: absolute;
        inset: -4px;
        border-radius: 50%;
        border: 2px solid ${PRIMARY_COLOR};
        opacity: 0;
        animation: sia-ring-idle 3s ease-in-out infinite;
      }
      @keyframes sia-ring-idle {
        0%, 100% { transform: scale(1); opacity: 0; }
        50% { transform: scale(1.15); opacity: 0.4; }
      }

      #sia-widget-launcher.open::after { animation: none; opacity: 0; }

      /* Launcher icon transition */
      .sia-launcher-icon {
        position: relative; z-index: 2;
        width: 28px; height: 28px; fill: white;
        transition: transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease;
      }
      #sia-widget-launcher.open .sia-launcher-icon { transform: rotate(180deg) scale(0); opacity: 0; }
      .sia-launcher-close {
        position: absolute; z-index: 2;
        width: 24px; height: 24px; fill: white;
        transition: transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease;
        transform: rotate(-180deg) scale(0); opacity: 0;
      }
      #sia-widget-launcher.open .sia-launcher-close { transform: rotate(0deg) scale(1); opacity: 1; }

      /* Pulse animation */
      #sia-widget-launcher.pulse {
        animation: sia-pulse 2s ease-in-out infinite;
      }
      @keyframes sia-pulse {
        0%, 100% { box-shadow: var(--sia-shadow-launcher); }
        50% { box-shadow: 0 0 0 14px ${PRIMARY_COLOR}22, 0 0 0 28px ${PRIMARY_COLOR}11, var(--sia-shadow-launcher); }
      }

      /* Notification dot */
      .sia-notif-dot {
        position: absolute; top: 2px; right: 2px; z-index: 3;
        width: 14px; height: 14px; border-radius: 50%;
        background: #22c55e;
        border: 2.5px solid #1a1a2e;
        animation: sia-dot-pulse 2s ease-in-out infinite;
      }
      @keyframes sia-dot-pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.2); }
      }
      #sia-widget-launcher.open .sia-notif-dot { display: none; }

      /* ── Chat Window ── */
      #sia-widget-window {
        position: fixed; bottom: 104px; right: 28px; z-index: 99999;
        width: 400px; max-height: 600px; height: 600px;
        background: var(--sia-bg-dark);
        border-radius: 20px;
        box-shadow: var(--sia-shadow);
        display: flex; flex-direction: column; overflow: hidden;
        font-family: var(--sia-font);
        border: 1px solid var(--sia-glass-border);
        /* Animation: closed by default */
        opacity: 0;
        transform: translateY(24px) scale(0.92);
        pointer-events: none;
        transition: opacity 0.45s cubic-bezier(0.34, 1.56, 0.64, 1),
                    transform 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
      }
      #sia-widget-window.open {
        opacity: 1;
        transform: translateY(0) scale(1);
        pointer-events: auto;
      }
      #sia-widget-window.closing {
        opacity: 0;
        transform: translateY(16px) scale(0.95);
        pointer-events: none;
        transition: opacity 0.3s ease, transform 0.3s ease;
      }

      /* ── Header ── */
      #sia-widget-header {
        background: var(--sia-gradient);
        padding: 18px 20px; display: flex; align-items: center; gap: 14px;
        color: white; flex-shrink: 0;
        position: relative; overflow: hidden;
      }
      /* Header shimmer animation */
      #sia-widget-header::before {
        content: '';
        position: absolute; top: 0; left: -100%;
        width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
        animation: sia-header-shimmer 4s ease-in-out infinite;
      }
      @keyframes sia-header-shimmer {
        0% { left: -100%; }
        50% { left: 100%; }
        100% { left: 100%; }
      }

      #sia-widget-avatar {
        width: 44px; height: 44px; border-radius: 14px;
        background: rgba(255,255,255,0.18); backdrop-filter: blur(8px);
        display: flex; align-items: center; justify-content: center;
        font-size: 22px; font-weight: 800; color: white; flex-shrink: 0;
        position: relative; z-index: 1;
        border: 1px solid rgba(255,255,255,0.2);
        transition: transform 0.3s ease;
      }
      #sia-widget-avatar:hover { transform: rotate(10deg) scale(1.1); }
      
      #sia-widget-header-info { position: relative; z-index: 1; }
      #sia-widget-header-info h3 {
        margin: 0; font-size: 15px; font-weight: 700; line-height: 1.3;
        letter-spacing: 0.3px;
      }
      #sia-widget-header-info .sia-subline {
        display: flex; align-items: center; gap: 6px;
        margin: 3px 0 0; font-size: 12px; opacity: 0.9; line-height: 1.2;
        font-weight: 400;
      }
      .sia-online-dot {
        width: 7px; height: 7px; border-radius: 50%; background: #22c55e;
        display: inline-block;
        animation: sia-online-blink 2.5s ease-in-out infinite;
      }
      @keyframes sia-online-blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
      }

      #sia-widget-close {
        margin-left: auto; background: rgba(255,255,255,0.12); border: none; color: white;
        width: 32px; height: 32px; border-radius: 10px;
        display: flex; align-items:center; justify-content: center;
        font-size: 18px; cursor: pointer; line-height: 1;
        transition: all 0.25s ease; position: relative; z-index: 1;
      }
      #sia-widget-close:hover {
        background: rgba(255,255,255,0.25);
        transform: rotate(90deg);
      }

      /* ── Messages Area ── */
      #sia-widget-messages {
        flex: 1; overflow-y: auto; padding: 18px 16px;
        display: flex; flex-direction: column; gap: 8px;
        background: var(--sia-bg-dark);
        scroll-behavior: smooth;
      }
      #sia-widget-messages::-webkit-scrollbar { width: 4px; }
      #sia-widget-messages::-webkit-scrollbar-track { background: transparent; }
      #sia-widget-messages::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 4px; }

      /* ── Message Bubbles ── */
      .sia-msg {
        max-width: 82%; padding: 12px 16px; border-radius: 16px;
        font-size: 14px; line-height: 1.6; word-wrap: break-word;
        position: relative; font-weight: 400;
        letter-spacing: 0.1px;
      }
      .sia-msg.bot {
        align-self: flex-start;
        background: var(--sia-glass);
        color: var(--sia-text-primary);
        border: 1px solid var(--sia-glass-border);
        border-bottom-left-radius: 4px;
        backdrop-filter: blur(8px);
        /* Entrance animation */
        animation: sia-msg-bot-in 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
        opacity: 0;
      }
      @keyframes sia-msg-bot-in {
        from { opacity: 0; transform: translateX(-12px) scale(0.95); }
        to   { opacity: 1; transform: translateX(0) scale(1); }
      }

      .sia-msg.user {
        align-self: flex-end;
        background: var(--sia-gradient);
        color: white;
        border-bottom-right-radius: 4px;
        font-weight: 500;
        box-shadow: 0 4px 16px rgba(209,28,93,0.25);
        animation: sia-msg-user-in 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
        opacity: 0;
      }
      @keyframes sia-msg-user-in {
        from { opacity: 0; transform: translateX(12px) scale(0.95); }
        to   { opacity: 1; transform: translateX(0) scale(1); }
      }

      /* Rendered (no animation for history) */
      .sia-msg.rendered { animation: none; opacity: 1; }

      /* ── Typewriter cursor ── */
      .sia-typewriter-cursor {
        display: inline-block;
        width: 2px; height: 16px;
        background: ${PRIMARY_COLOR};
        margin-left: 2px;
        vertical-align: text-bottom;
        animation: sia-cursor-blink 0.7s ease-in-out infinite;
      }
      @keyframes sia-cursor-blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0; }
      }

      /* ── Typing Indicator (3-dot wave) ── */
      .sia-typing {
        align-self: flex-start; display: flex; gap: 5px; padding: 14px 18px;
        background: var(--sia-glass);
        border: 1px solid var(--sia-glass-border);
        border-radius: 16px; border-bottom-left-radius: 4px;
        backdrop-filter: blur(8px);
        animation: sia-msg-bot-in 0.3s ease forwards;
        opacity: 0;
      }
      .sia-typing-dot {
        width: 8px; height: 8px; border-radius: 50%;
        background: var(--sia-text-secondary);
        animation: sia-wave 1.4s ease-in-out infinite;
      }
      .sia-typing-dot:nth-child(2) { animation-delay: 0.15s; }
      .sia-typing-dot:nth-child(3) { animation-delay: 0.3s; }
      @keyframes sia-wave {
        0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
        30% { transform: translateY(-8px); opacity: 1; }
      }

      /* ── Quick Reply Chips ── */
      .sia-chips {
        display: flex; flex-wrap: wrap; gap: 7px; margin-top: 6px;
        align-self: flex-start; max-width: 92%;
        animation: sia-chips-in 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
        opacity: 0;
      }
      @keyframes sia-chips-in {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
      }
      .sia-chip {
        background: transparent;
        border: 1.5px solid rgba(209,28,93,0.5);
        color: #f0a0c0;
        padding: 8px 16px; border-radius: 24px; font-size: 13px; font-weight: 500;
        cursor: pointer; white-space: nowrap;
        font-family: var(--sia-font); line-height: 1.3;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        position: relative; overflow: hidden;
      }
      .sia-chip::before {
        content: '';
        position: absolute; inset: 0;
        background: var(--sia-gradient);
        opacity: 0;
        transition: opacity 0.3s ease;
        border-radius: 24px;
      }
      .sia-chip:hover::before { opacity: 1; }
      .sia-chip:hover {
        color: white; border-color: transparent;
        transform: translateY(-2px) scale(1.04);
        box-shadow: 0 6px 20px rgba(209,28,93,0.35);
      }
      .sia-chip span { position: relative; z-index: 1; }
      .sia-chip:active { transform: scale(0.95); }

      /* Stagger chip animation */
      .sia-chip:nth-child(1) { animation: sia-chip-pop 0.4s 0.1s cubic-bezier(0.34,1.56,0.64,1) forwards; opacity: 0; }
      .sia-chip:nth-child(2) { animation: sia-chip-pop 0.4s 0.2s cubic-bezier(0.34,1.56,0.64,1) forwards; opacity: 0; }
      .sia-chip:nth-child(3) { animation: sia-chip-pop 0.4s 0.3s cubic-bezier(0.34,1.56,0.64,1) forwards; opacity: 0; }
      .sia-chip:nth-child(4) { animation: sia-chip-pop 0.4s 0.4s cubic-bezier(0.34,1.56,0.64,1) forwards; opacity: 0; }
      .sia-chip:nth-child(5) { animation: sia-chip-pop 0.4s 0.5s cubic-bezier(0.34,1.56,0.64,1) forwards; opacity: 0; }
      @keyframes sia-chip-pop {
        from { opacity: 0; transform: scale(0.6) translateY(8px); }
        to   { opacity: 1; transform: scale(1) translateY(0); }
      }

      /* ── Input Area ── */
      #sia-widget-input-area {
        padding: 14px 16px;
        border-top: 1px solid var(--sia-glass-border);
        display: flex; gap: 10px; align-items: center;
        background: rgba(22,33,62,0.95);
        backdrop-filter: blur(10px);
        flex-shrink: 0;
      }
      #sia-widget-input {
        flex: 1;
        border: 1.5px solid var(--sia-glass-border);
        border-radius: 28px;
        padding: 12px 20px; font-size: 14px; outline: none;
        font-family: var(--sia-font); font-weight: 400;
        background: var(--sia-glass);
        color: var(--sia-text-primary);
        transition: all 0.3s ease;
        letter-spacing: 0.2px;
      }
      #sia-widget-input:focus {
        border-color: ${PRIMARY_COLOR};
        background: rgba(255,255,255,0.08);
        box-shadow: 0 0 0 3px ${PRIMARY_COLOR}22;
      }
      #sia-widget-input::placeholder { color: var(--sia-text-secondary); }

      #sia-widget-send {
        width: 42px; height: 42px; border-radius: 50%; border: none;
        background: var(--sia-gradient);
        color: white; cursor: pointer;
        display: flex; align-items: center; justify-content: center;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        flex-shrink: 0;
        box-shadow: 0 4px 12px rgba(209,28,93,0.3);
      }
      #sia-widget-send:hover {
        transform: scale(1.1) rotate(15deg);
        box-shadow: 0 6px 20px rgba(209,28,93,0.45);
      }
      #sia-widget-send:active { transform: scale(0.9); }
      #sia-widget-send svg { width: 18px; height: 18px; fill: white; position: relative; z-index: 1; }

      /* ── Emoji button ── */
      #sia-widget-emoji-btn {
        width: 36px; height: 36px; border-radius: 50%; border: none;
        background: transparent; color: var(--sia-text-secondary); cursor: pointer;
        display: flex; align-items: center; justify-content: center;
        font-size: 20px; transition: all 0.3s ease; flex-shrink: 0;
      }
      #sia-widget-emoji-btn:hover { color: #f0f0f0; transform: scale(1.15); }

      /* ── Powered By ── */
      #sia-widget-powered {
        text-align: center; padding: 8px; font-size: 11px;
        color: var(--sia-text-secondary);
        background: rgba(22,33,62,0.95);
        flex-shrink: 0;
        letter-spacing: 0.3px;
        font-weight: 400;
      }
      #sia-widget-powered a {
        color: ${PRIMARY_COLOR}; text-decoration: none; font-weight: 600;
        transition: color 0.2s ease;
      }
      #sia-widget-powered a:hover { color: ${SECONDARY_COLOR}; }

      /* ── Timestamp separator ── */
      .sia-timestamp {
        text-align: center; font-size: 11px; color: var(--sia-text-secondary);
        padding: 8px 0; font-weight: 500; letter-spacing: 0.5px;
        opacity: 0.7;
      }

      /* ── Welcome overlay animation ── */
      .sia-welcome-overlay {
        position: absolute; inset: 0; z-index: 10;
        background: var(--sia-gradient);
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        animation: sia-welcome-fade 0.8s 1.5s ease forwards;
        opacity: 1; pointer-events: none;
      }
      @keyframes sia-welcome-fade {
        to { opacity: 0; }
      }
      .sia-welcome-logo {
        font-size: 48px; font-weight: 800; color: white;
        animation: sia-welcome-pop 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
      }
      .sia-welcome-text {
        font-size: 14px; color: rgba(255,255,255,0.8);
        margin-top: 8px; font-weight: 400;
        animation: sia-welcome-pop 0.6s 0.2s cubic-bezier(0.34, 1.56, 0.64, 1) both;
      }
      @keyframes sia-welcome-pop {
        from { opacity: 0; transform: scale(0.5); }
        to   { opacity: 1; transform: scale(1); }
      }

      /* ── Particle background in header ── */
      .sia-particles {
        position: absolute; inset: 0; overflow: hidden; pointer-events: none;
      }
      .sia-particle {
        position: absolute; width: 4px; height: 4px;
        background: rgba(255,255,255,0.15); border-radius: 50%;
        animation: sia-float 6s ease-in-out infinite;
      }
      .sia-particle:nth-child(1) { top: 20%; left: 10%; animation-delay: 0s; animation-duration: 5s; }
      .sia-particle:nth-child(2) { top: 60%; left: 80%; animation-delay: 1s; animation-duration: 7s; }
      .sia-particle:nth-child(3) { top: 40%; left: 50%; animation-delay: 2s; animation-duration: 6s; }
      .sia-particle:nth-child(4) { top: 80%; left: 30%; animation-delay: 0.5s; animation-duration: 8s; }
      .sia-particle:nth-child(5) { top: 10%; left: 70%; animation-delay: 1.5s; animation-duration: 5.5s; }
      @keyframes sia-float {
        0%, 100% { transform: translateY(0) translateX(0); opacity: 0.3; }
        25% { transform: translateY(-8px) translateX(4px); opacity: 0.6; }
        50% { transform: translateY(-4px) translateX(-3px); opacity: 0.4; }
        75% { transform: translateY(-10px) translateX(2px); opacity: 0.5; }
      }

      /* ── Mobile Responsive ── */
      @media (max-width: 480px) {
        #sia-widget-window {
          width: calc(100vw - 16px); right: 8px; bottom: 88px;
          max-height: calc(100vh - 108px); height: calc(100vh - 108px);
          border-radius: 16px;
        }
        #sia-widget-launcher { bottom: 18px; right: 18px; width: 58px; height: 58px; }
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
    launcher.innerHTML = `
      <svg class="sia-launcher-icon" viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/><path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg>
      <svg class="sia-launcher-close" viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
      <div class="sia-notif-dot"></div>
    `;
    launcher.onclick = toggleWidget;
    document.body.appendChild(launcher);

    // Chat window
    const win = document.createElement("div");
    win.id = "sia-widget-window";
    win.innerHTML = `
      <div id="sia-widget-header">
        <div class="sia-particles">
          <div class="sia-particle"></div>
          <div class="sia-particle"></div>
          <div class="sia-particle"></div>
          <div class="sia-particle"></div>
          <div class="sia-particle"></div>
        </div>
        <div id="sia-widget-avatar">✦</div>
        <div id="sia-widget-header-info">
          <h3>${BOT_NAME} — SSSi Assistant</h3>
          <div class="sia-subline">
            <span class="sia-online-dot"></span>
            <span>Online • Replies instantly</span>
          </div>
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
  let firstOpen = true;

  function toggleWidget() {
    const win = document.getElementById("sia-widget-window");
    const launcher = document.getElementById("sia-widget-launcher");

    if (!widgetOpen) {
      // OPEN
      widgetOpen = true;
      launcher.classList.add("open");
      win.classList.remove("closing");

      // Show welcome overlay on first open
      if (firstOpen) {
        firstOpen = false;
        const overlay = document.createElement("div");
        overlay.className = "sia-welcome-overlay";
        overlay.innerHTML = `
          <div class="sia-welcome-logo">✦</div>
          <div class="sia-welcome-text">${BOT_NAME} is ready to help</div>
        `;
        win.appendChild(overlay);
        setTimeout(() => overlay.remove(), 2500);
      }

      // Trigger open animation
      requestAnimationFrame(() => {
        win.classList.add("open");
      });

      launcher.classList.remove("pulse");
      stopPulse();

      if (messages.length === 0) {
        setTimeout(() => showWelcomeMessage(), firstOpen ? 0 : 600);
      } else {
        renderAllMessages();
      }

      const input = document.getElementById("sia-widget-input");
      setTimeout(() => input && input.focus(), 500);
      resetInactivityTimer();
    } else {
      // CLOSE with animation
      widgetOpen = false;
      launcher.classList.remove("open");
      win.classList.remove("open");
      win.classList.add("closing");
      clearInactivityTimer();

      setTimeout(() => {
        win.classList.remove("closing");
      }, 350);
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

    addBotMessage(greeting, chips, true); // true = typewriter
  }

  /* ── Message Rendering ─────────────────────────────────────────── */
  function addBotMessage(text, chips, useTypewriter) {
    messages.push({ role: "bot", text, chips: chips || [] });
    persistState();

    if (useTypewriter && !isTypewriting) {
      renderMessageWithTypewriter({ role: "bot", text, chips: chips || [] });
    } else {
      renderMessage({ role: "bot", text, chips: chips || [] });
    }
    scrollToBottom();
  }

  function addUserMessage(text) {
    messages.push({ role: "user", text });
    persistState();
    renderMessage({ role: "user", text });
    scrollToBottom();
  }

  function renderMessage(msg, skipAnimation) {
    const container = document.getElementById("sia-widget-messages");
    if (!container) return;

    if (msg.role === "user") {
      const div = document.createElement("div");
      div.className = "sia-msg user" + (skipAnimation ? " rendered" : "");
      div.textContent = msg.text;
      container.appendChild(div);
    } else {
      const div = document.createElement("div");
      div.className = "sia-msg bot" + (skipAnimation ? " rendered" : "");
      div.innerHTML = formatBotHtml(msg.text);
      container.appendChild(div);

      // Chips
      if (msg.chips && msg.chips.length > 0) {
        renderChips(msg.chips, container, skipAnimation);
      }
    }
  }

  function renderChips(chips, container, skipAnimation) {
    const chipContainer = document.createElement("div");
    chipContainer.className = "sia-chips" + (skipAnimation ? " rendered" : "");
    if(skipAnimation) chipContainer.style.opacity = "1";
    chips.forEach(label => {
      const btn = document.createElement("button");
      btn.className = "sia-chip";
      btn.innerHTML = `<span>${escapeHtml(label)}</span>`;
      if(skipAnimation) { btn.style.opacity = "1"; btn.style.animation = "none"; }
      btn.onclick = () => handleChipClick(label);
      chipContainer.appendChild(btn);
    });
    container.appendChild(chipContainer);
  }

  /* ── Typewriter Effect ──────────────────────────────────────────── */
  function renderMessageWithTypewriter(msg) {
    const container = document.getElementById("sia-widget-messages");
    if (!container) return;

    isTypewriting = true;

    const div = document.createElement("div");
    div.className = "sia-msg bot";
    div.innerHTML = '<span class="sia-typewriter-cursor"></span>';
    container.appendChild(div);
    scrollToBottom();

    const fullHtml = formatBotHtml(msg.text);
    const fullText = msg.text;
    let charIndex = 0;

    function typeNext() {
      if (charIndex < fullText.length) {
        // Build the HTML up to current position
        const partialText = fullText.substring(0, charIndex + 1);
        div.innerHTML = formatBotHtml(partialText) + '<span class="sia-typewriter-cursor"></span>';
        charIndex++;
        scrollToBottom();

        // Variable speed: pause longer on punctuation
        let delay = TYPEWRITER_CHAR_MS;
        const currentChar = fullText[charIndex - 1];
        if (currentChar === '.' || currentChar === '!' || currentChar === '?') delay = 120;
        else if (currentChar === ',') delay = 60;
        else if (currentChar === ' ') delay = 10;

        setTimeout(typeNext, delay);
      } else {
        // Done typing — remove cursor, add chips
        div.innerHTML = fullHtml;
        isTypewriting = false;

        if (msg.chips && msg.chips.length > 0) {
          setTimeout(() => {
            renderChips(msg.chips, container, false);
            scrollToBottom();
          }, 200);
        }
      }
    }

    // Start after a brief pause
    setTimeout(typeNext, 300);
  }

  function renderAllMessages() {
    const container = document.getElementById("sia-widget-messages");
    if (!container) return;
    container.innerHTML = "";
    messages.forEach(msg => renderMessage(msg, true));
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
    // Disable all chips after click
    document.querySelectorAll(".sia-chips").forEach(c => {
      const last = document.getElementById("sia-widget-messages").lastElementChild;
      if (c === last || c === last?.previousElementSibling) {
        c.querySelectorAll(".sia-chip").forEach(b => {
          b.disabled = true; b.style.opacity = "0.35"; b.style.cursor = "default";
          b.style.pointerEvents = "none";
        });
      }
    });
    handleSend(label);
  }

  /* ── Extract Session State from AI Response ────────────────────── */
  function extractStateFromResponse(botText, userText) {
    const lower = (userText || "").toLowerCase();

    // IMPORTANT: Check higher classes FIRST to prevent "class 11" matching "class 1"
    if (/class\s*11[\s\-–]12|\bclass\s*11\b|\bclass\s*12\b|11th|12th/i.test(lower)) sessionState.grade = "Class 11-12";
    else if (/class\s*9[\s\-–]10|\bclass\s*9\b|\bclass\s*10\b|10th/i.test(lower)) sessionState.grade = "Class 9-10";
    else if (/class\s*6[\s\-–]8|\bclass\s*6\b|\bclass\s*7\b|\bclass\s*8\b/i.test(lower)) sessionState.grade = "Class 6-8";
    else if (/class\s*1[\s\-–]5|\bclass\s*[1-5]\b/i.test(lower)) sessionState.grade = "Class 1-5";
    else if (/college|grad|undergraduate|postgrad/i.test(lower)) sessionState.grade = "College/Grad";
    else if (/professional|working/i.test(lower)) sessionState.grade = "Working Professional";

    if (/\bcbse\b/i.test(lower)) sessionState.board = "CBSE";
    else if (/\bicse\b/i.test(lower)) sessionState.board = "ICSE";
    else if (/\bib\b/i.test(lower)) sessionState.board = "IB";
    else if (/\bigcse\b/i.test(lower)) sessionState.board = "IGCSE";
    else if (/\bcambridge\b/i.test(lower)) sessionState.board = "Cambridge";
    else if (/state\s*board/i.test(lower)) sessionState.board = "State Board";

    // Subject keyword → display name. Uses word-boundary matching for short/ambiguous keywords.
    const subjectMap = [
      ["maths",            "Maths"],
      ["math",             "Maths"],
      ["physics",          "Physics"],
      ["chemistry",        "Chemistry"],
      ["biology",          "Biology"],
      ["english",          "English"],
      ["hindi",            "Hindi"],
      ["social studies",   "Social Studies"],
      ["social science",   "Social Science"],
      ["computer science", "Computer Science"],
      ["accountancy",      "Accountancy"],
      ["economics",        "Economics"],
      ["business studies", "Business Studies"],
      ["coding",           "Coding"],
      ["data science",     "Data Science/AI"],
      ["digital marketing","Digital Marketing"],
      // Use word-boundary for "ai" so it does NOT match "email", "gmail", "paid", etc.
      ["\\bai\\b",         "AI & ML"],
      ["\\bml\\b",         "AI & ML"],
      ["artificial intelligence", "AI & ML"],
      ["machine learning", "AI & ML"],
    ];
    subjectMap.forEach(([kw, name]) => {
      // Multi-word or already-regex patterns use RegExp; single words use plain includes for speed
      const matched = kw.startsWith("\\b") || kw.includes(" ")
        ? new RegExp(kw, "i").test(lower)
        : lower.includes(kw);
      if (matched && !sessionState.subjects.includes(name)) {
        sessionState.subjects.push(name);
      }
    });
    if (/all subjects/i.test(lower)) sessionState.subjects = ["All Subjects"];

    if (/jee/i.test(lower) && !sessionState.goal) sessionState.goal = "IIT-JEE";
    else if (/neet/i.test(lower) && !sessionState.goal) sessionState.goal = "NEET";
    else if (/olympiad/i.test(lower) && !sessionState.goal) sessionState.goal = "Olympiad";
    else if (/competitive\s*exam/i.test(lower) && !sessionState.goal) sessionState.goal = "Competitive Exam";
    else if (/school exam|score better/i.test(lower) && !sessionState.goal) sessionState.goal = "School Exams";
    else if (/skill building|skill/i.test(lower) && !sessionState.goal) sessionState.goal = "Skill Building";
    else if (/general improvement/i.test(lower) && !sessionState.goal) sessionState.goal = "General Improvement";

    if (/\b(my child|my son|my daughter|parent|my kid)\b/i.test(lower)) sessionState.user_type = "parent";

    if (/demo booked|✅.*name:/i.test(botText)) {
      const nameMatch = botText.match(/👤\s*Name:\s*(.+?)[\n📚]/);
      if (nameMatch) sessionState.name = nameMatch[1].trim();
    }
    // Extract name from explicit patterns in user message: "my name is X", "I'm X", "this is X", "call me X"
    if (!sessionState.name) {
      const explicitName = userText.match(/(?:my name is|i'?m|this is|call me|i am)\s+([A-Za-z][a-zA-Z]*(?:\s+[A-Za-z][a-zA-Z]*){0,2})/i);
      if (explicitName) {
        sessionState.name = explicitName[1].trim().replace(/\b\w/g, c => c.toUpperCase());
      }
    }
    // Extract name when bot asked for it — ONLY on pre-send call (botText is empty)
    // This prevents false captures like "YES" being treated as a name when the bot's
    // RESPONSE (not the user's reply) contains a name prompt.
    const NOT_NAMES = /^(yes|no|ok|okay|sure|hi|hey|hello|thanks|thank|ya|yep|yup|nope|nah|hmm|hm|fine|great|good|nice|cool|awesome|please|help|skip|done|cancel|stop|start|book|demo|free|class|more|other|next|back|bye|hii|okk)$/i;
    if (!botText && !sessionState.name && /^[A-Za-z][a-zA-Z]{1,20}(\s+[A-Za-z][a-zA-Z]{1,20}){0,2}$/.test(userText.trim()) && !NOT_NAMES.test(userText.trim())) {
      const lastBot = messages.filter(m => m.role === "bot").slice(-1)[0];
      if (lastBot && /(what('?s| is) your (good )?name|share your name|may i (have|know|get) your name|could (you|i) (tell|share|give|get|have).*name|your (good )?name|tell me your name|name please|who am i speaking|can i (get|have|know) your name|let me know your name|know your name|get your name)/i.test(lastBot.text)) {
        sessionState.name = userText.trim().replace(/\b\w/g, c => c.toUpperCase());
      }
    }

    const phoneMatch = lower.match(/(?:\+?91[\s-]?)?([6-9]\d{9})/);
    if (phoneMatch && !sessionState.phone) sessionState.phone = phoneMatch[1];

    // Extract email from user message
    const emailMatch = userText.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
    if (emailMatch && !sessionState.email) sessionState.email = emailMatch[0].toLowerCase();

    if (/morning|8am|8\s*am/i.test(lower)) sessionState.preferred_time = "Morning 8AM-12PM";
    else if (/afternoon|12pm|12\s*pm|1pm|2pm|3pm/i.test(lower)) sessionState.preferred_time = "Afternoon 12PM-4PM";
    else if (/evening|4pm|5pm|6pm|7pm|8pm/i.test(lower)) sessionState.preferred_time = "Evening 4PM-8PM";

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
      tenant_id: ORG_ID, visitor_id: visitorId,
      name: sessionState.name, phone: sessionState.phone,
      email: sessionState.email,
      grade: sessionState.grade, board: sessionState.board,
      subjects: sessionState.subjects, goal: sessionState.goal,
      user_type: sessionState.user_type, preferred_time: sessionState.preferred_time,
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
      sessionState.lead_captured = false;
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
    extractStateFromResponse("", text);
    showTyping();
    resetInactivityTimer();

    try {
      const payload = {
        tenant_id: ORG_ID, visitor_id: visitorId,
        message: text, session_state: sessionState,
      };

      const res = await fetch(API_BASE + "/api/v1/chatbot/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      const botResponse = data.response || data.message || "I'm having trouble — please try again!";

      await new Promise(resolve => setTimeout(resolve, randomDelay()));
      hideTyping();

      const { cleanText, chips } = parseChips(botResponse);
      addBotMessage(cleanText || botResponse, chips, true); // typewriter enabled

      extractStateFromResponse(botResponse, text);
      attemptLeadCapture();

    } catch (err) {
      console.error("[Sia] API error:", err);
      hideTyping();
      addBotMessage("Oops — something went wrong! Please try again or reach us at sssi.in 📞", [], false);
    }
  }

  /* ── Inactivity Nudge ──────────────────────────────────────────── */
  function resetInactivityTimer() {
    clearInactivityTimer();
    inactivityTimer = setTimeout(() => {
      if (widgetOpen && !isTyping) {
        addBotMessage("Still there? No rush — just tap any option below when you're ready! 😊",
          ["📅 Book Free Demo", "💰 Pricing", "📞 Talk to Counselor"], true);
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
