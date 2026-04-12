(function () {
  "use strict";

  const script = document.currentScript;
  const ORG_ID = script.getAttribute("data-org") || "default";
  const COLOR = script.getAttribute("data-color") || "#4F46E5";
  const BOT_NAME = script.getAttribute("data-name") || "Aria";
  const API_BASE =
    script.getAttribute("data-api") ||
    "https://ravian-backend-production.railway.app";

  // ── Session management ──────────────────────────────────────
  let sessionId = localStorage.getItem("ravian_session_" + ORG_ID);
  if (!sessionId) {
    sessionId = "sess_" + Math.random().toString(36).substr(2, 12);
    localStorage.setItem("ravian_session_" + ORG_ID, sessionId);
  }

  // ── Color helpers ───────────────────────────────────────────
  function hexToRgb(hex) {
    var r = parseInt(hex.slice(1, 3), 16);
    var g = parseInt(hex.slice(3, 5), 16);
    var b = parseInt(hex.slice(5, 7), 16);
    return r + "," + g + "," + b;
  }
  var colorRgb = hexToRgb(COLOR);

  // ── Inject styles ──────────────────────────────────────────
  var style = document.createElement("style");
  style.textContent =
    '#ravian-widget-btn{position:fixed;bottom:24px;right:24px;width:60px;height:60px;border-radius:50%;background:' + COLOR + ';color:#fff;border:none;cursor:pointer;font-size:24px;box-shadow:0 4px 20px rgba(' + colorRgb + ',0.4);z-index:99999;transition:all .3s cubic-bezier(.4,0,.2,1);display:flex;align-items:center;justify-content:center}' +
    '#ravian-widget-btn:hover{transform:scale(1.1);box-shadow:0 6px 28px rgba(' + colorRgb + ',0.5)}' +
    '#ravian-widget-btn.open{transform:rotate(90deg) scale(1.1)}' +
    '#ravian-chat-box{position:fixed;bottom:100px;right:24px;width:380px;height:540px;background:#fff;border-radius:20px;box-shadow:0 12px 48px rgba(0,0,0,0.15);z-index:99998;display:none;flex-direction:column;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;overflow:hidden;animation:ravian-slideUp .3s ease}' +
    '@keyframes ravian-slideUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}' +
    '#ravian-chat-header{background:linear-gradient(135deg,' + COLOR + ',' + COLOR + 'dd);color:#fff;padding:18px 20px;font-weight:600;font-size:15px;display:flex;align-items:center;gap:10px}' +
    '#ravian-chat-header .ravian-avatar{width:36px;height:36px;border-radius:50%;background:rgba(255,255,255,0.2);display:flex;align-items:center;justify-content:center;font-size:18px}' +
    '#ravian-chat-header .ravian-header-text{display:flex;flex-direction:column}' +
    '#ravian-chat-header .ravian-header-name{font-size:15px;font-weight:600}' +
    '#ravian-chat-header .ravian-header-status{font-size:11px;opacity:0.85;font-weight:400}' +
    '#ravian-chat-messages{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:10px;background:#f8fafc}' +
    '#ravian-chat-messages::-webkit-scrollbar{width:4px}' +
    '#ravian-chat-messages::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:4px}' +
    '.ravian-msg{max-width:82%;padding:11px 15px;border-radius:16px;font-size:14px;line-height:1.5;word-wrap:break-word;animation:ravian-fadeIn .25s ease}' +
    '@keyframes ravian-fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}' +
    '.ravian-msg.bot{background:#fff;color:#1e293b;align-self:flex-start;border-bottom-left-radius:4px;box-shadow:0 1px 3px rgba(0,0,0,0.06)}' +
    '.ravian-msg.user{background:' + COLOR + ';color:#fff;align-self:flex-end;border-bottom-right-radius:4px}' +
    '#ravian-chat-input-row{display:flex;padding:12px 14px;border-top:1px solid #e2e8f0;gap:8px;background:#fff}' +
    '#ravian-input{flex:1;padding:10px 16px;border-radius:24px;border:1.5px solid #e2e8f0;outline:none;font-size:14px;font-family:inherit;transition:border-color .2s}' +
    '#ravian-input:focus{border-color:' + COLOR + '}' +
    '#ravian-input::placeholder{color:#94a3b8}' +
    '#ravian-send{background:' + COLOR + ';color:#fff;border:none;border-radius:50%;width:40px;height:40px;min-width:40px;cursor:pointer;font-size:18px;display:flex;align-items:center;justify-content:center;transition:all .2s}' +
    '#ravian-send:hover{opacity:0.9;transform:scale(1.05)}' +
    '#ravian-send:disabled{opacity:0.5;cursor:not-allowed;transform:none}' +
    '.ravian-typing{display:flex;gap:4px;align-items:center;padding:11px 15px}' +
    '.ravian-dot{width:7px;height:7px;border-radius:50%;background:#94a3b8;animation:ravian-bounce 1.2s infinite}' +
    '.ravian-dot:nth-child(2){animation-delay:.2s}' +
    '.ravian-dot:nth-child(3){animation-delay:.4s}' +
    '@keyframes ravian-bounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-8px)}}' +
    '.ravian-powered{text-align:center;padding:6px;font-size:10px;color:#94a3b8;background:#fff}' +
    '@media(max-width:480px){#ravian-chat-box{width:calc(100vw - 20px);height:calc(100vh - 120px);right:10px;bottom:80px;border-radius:16px}#ravian-widget-btn{bottom:16px;right:16px;width:54px;height:54px;font-size:22px}}';
  document.head.appendChild(style);

  // ── Inject HTML ────────────────────────────────────────────
  document.body.insertAdjacentHTML(
    "beforeend",
    '<button id="ravian-widget-btn" aria-label="Open chat">💬</button>' +
    '<div id="ravian-chat-box">' +
      '<div id="ravian-chat-header">' +
        '<div class="ravian-avatar">🤖</div>' +
        '<div class="ravian-header-text">' +
          '<span class="ravian-header-name">' + BOT_NAME + '</span>' +
          '<span class="ravian-header-status">● Online</span>' +
        '</div>' +
      '</div>' +
      '<div id="ravian-chat-messages"></div>' +
      '<div id="ravian-chat-input-row">' +
        '<input id="ravian-input" placeholder="Type a message..." autocomplete="off" />' +
        '<button id="ravian-send" aria-label="Send message">➤</button>' +
      '</div>' +
      '<div class="ravian-powered">Powered by Ravian AI</div>' +
    '</div>'
  );

  var btn = document.getElementById("ravian-widget-btn");
  var box = document.getElementById("ravian-chat-box");
  var messages = document.getElementById("ravian-chat-messages");
  var input = document.getElementById("ravian-input");
  var sendBtn = document.getElementById("ravian-send");

  var isOpen = false;
  var isFirstOpen = true;
  var isSending = false;

  // ── Message helpers ────────────────────────────────────────
  function addMessage(text, role) {
    var msg = document.createElement("div");
    msg.className = "ravian-msg " + role;
    msg.textContent = text;
    messages.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
  }

  function showTyping() {
    var t = document.createElement("div");
    t.id = "ravian-typing";
    t.className = "ravian-msg bot ravian-typing";
    t.innerHTML =
      '<div class="ravian-dot"></div><div class="ravian-dot"></div><div class="ravian-dot"></div>';
    messages.appendChild(t);
    messages.scrollTop = messages.scrollHeight;
    return t;
  }

  // ── Send message ───────────────────────────────────────────
  async function sendMessage(text) {
    if (isSending) return;
    isSending = true;
    sendBtn.disabled = true;

    addMessage(text, "user");
    input.value = "";
    var typing = showTyping();

    try {
      var res = await fetch(API_BASE + "/api/v1/chatbot/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          session_id: sessionId,
          tenant_id: ORG_ID,
          page_url: window.location.href,
        }),
      });
      var data = await res.json();
      typing.remove();

      // GPT reply
      var reply = data.reply || data.response || data.message || "Sorry, something went wrong.";
      addMessage(reply, "bot");

      // Store last program for return visitor recognition
      if (data.program_interest) {
        localStorage.setItem("ravian_program_" + ORG_ID, data.program_interest);
      }
    } catch (e) {
      typing.remove();
      addMessage(
        "Sorry, I'm having trouble connecting right now. Please try again in a moment! 🔄",
        "bot"
      );
      console.error("[Ravian Widget] Error:", e);
    } finally {
      isSending = false;
      sendBtn.disabled = false;
      input.focus();
    }
  }

  // ── Event listeners ────────────────────────────────────────
  btn.addEventListener("click", function () {
    isOpen = !isOpen;
    box.style.display = isOpen ? "flex" : "none";
    btn.textContent = isOpen ? "✕" : "💬";
    btn.classList.toggle("open", isOpen);

    if (isOpen) {
      input.focus();
      // Welcome message on first open
      if (isFirstOpen) {
        isFirstOpen = false;
        // Check for returning visitor
        var lastProgram = localStorage.getItem("ravian_program_" + ORG_ID);
        var lastVisit = localStorage.getItem("ravian_last_visit_" + ORG_ID);
        if (lastVisit && lastProgram) {
          setTimeout(function () {
            addMessage(
              "Welcome back! 👋 Last time you were asking about " +
                lastProgram +
                ". Still interested? We have a batch starting soon!",
              "bot"
            );
          }, 400);
        } else {
          setTimeout(function () {
            addMessage(
              "Hi there! 👋 I'm " +
                BOT_NAME +
                ". Which program are you exploring today?",
              "bot"
            );
          }, 400);
        }
        localStorage.setItem(
          "ravian_last_visit_" + ORG_ID,
          new Date().toISOString()
        );
      }
    }
  });

  sendBtn.addEventListener("click", function () {
    if (input.value.trim()) sendMessage(input.value.trim());
  });

  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && input.value.trim() && !isSending) {
      sendMessage(input.value.trim());
    }
  });

  // ── Exit intent trigger ────────────────────────────────────
  var exitShown = false;
  document.addEventListener("mouseleave", function (e) {
    if (e.clientY <= 0 && !exitShown && !isOpen) {
      exitShown = true;
      isOpen = true;
      box.style.display = "flex";
      btn.textContent = "✕";
      btn.classList.add("open");
      isFirstOpen = false;
      localStorage.setItem(
        "ravian_last_visit_" + ORG_ID,
        new Date().toISOString()
      );
      addMessage(
        "Wait! 🎯 Before you go — want us to send you the program brochure? Just share your WhatsApp number and we'll send it right over!",
        "bot"
      );
    }
  });

  // ── Auto-open after 45 seconds if not opened ──────────────
  setTimeout(function () {
    if (!isOpen && isFirstOpen) {
      var pulse = document.createElement("div");
      pulse.style.cssText =
        "position:fixed;bottom:24px;right:24px;width:60px;height:60px;border-radius:50%;border:2px solid " +
        COLOR +
        ";z-index:99997;animation:ravian-pulse 2s ease-out infinite;pointer-events:none";
      var pulseStyle = document.createElement("style");
      pulseStyle.textContent =
        "@keyframes ravian-pulse{0%{transform:scale(1);opacity:0.6}100%{transform:scale(1.8);opacity:0}}";
      document.head.appendChild(pulseStyle);
      document.body.appendChild(pulse);

      // Remove pulse after 10 seconds
      setTimeout(function () {
        pulse.remove();
      }, 10000);
    }
  }, 45000);
})();
