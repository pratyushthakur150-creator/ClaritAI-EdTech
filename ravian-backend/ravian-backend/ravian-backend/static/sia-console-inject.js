/* SIA WIDGET v3.0 — Console Inject Version (paste this in DevTools console on sssi.in) */
/* Step 1: Type "allow pasting" in console first, then paste this entire block */

// Remove any existing widget
if(document.getElementById('sia-widget-launcher')) document.getElementById('sia-widget-launcher').remove();
if(document.getElementById('sia-widget-window')) document.getElementById('sia-widget-window').remove();
if(document.getElementById('sia-widget-styles')) document.getElementById('sia-widget-styles').remove();
Object.keys(localStorage).filter(k=>k.startsWith('sia_session')).forEach(k=>localStorage.removeItem(k));

(function(){
"use strict";
const ORG_ID="8a19c99f-3ebe-4c47-b483-b8796d122716";
const API_BASE="http://localhost:8000";
const PRIMARY_COLOR="#d11c5d";
const SECONDARY_COLOR="#7d3384";
const BOT_NAME="Sia";
const TYPING_MIN_MS=800;
const TYPING_MAX_MS=1500;
const TYPEWRITER_CHAR_MS=18;
const INACTIVITY_TIMEOUT_MS=60000;
const ATTENTION_PULSE_MS=45000;
const STORAGE_KEY="sia_session_"+ORG_ID.slice(0,8);

if(!document.querySelector('link[href*="Inter"]')){
const f=document.createElement("link");
f.href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap";
f.rel="stylesheet";document.head.appendChild(f);
}

let sessionState={grade:null,board:null,subjects:[],goal:null,name:null,phone:null,user_type:null,preferred_time:null,language:"English",lead_captured:false};
let visitorId="sia_"+Math.random().toString(36).slice(2,10)+"_"+Date.now();
let messages=[];
let widgetOpen=false;
let inactivityTimer=null;
let pulseTimer=null;
let isTyping=false;
let isTypewriting=false;

function persistState(){try{localStorage.setItem(STORAGE_KEY,JSON.stringify({visitorId,sessionState,messages:messages.slice(-30)}))}catch(e){}}
function getTimeOfDay(){const h=new Date().getHours();if(h>=6&&h<12)return"morning";if(h>=12&&h<18)return"afternoon";if(h>=18&&h<23)return"evening";return"night";}
function isHindi(t){return/[\u0900-\u097F]/.test(t)}
function isHinglish(t){const w=["kya","hai","kaise","mujhe","mera","kitna","haan","nahi","chahiye","padhai","bhai","yaar","accha","aur","batao"];return w.some(x=>t.toLowerCase().includes(x))}
function detectLanguage(t){if(isHindi(t))return"Hindi";if(isHinglish(t))return"Hinglish";return"English";}
function randomDelay(){return TYPING_MIN_MS+Math.random()*(TYPING_MAX_MS-TYPING_MIN_MS)}
function escapeHtml(s){const d=document.createElement("div");d.textContent=s;return d.innerHTML}

function parseChips(text){const r=/\[([^\[\]]{1,60})\]/g;const chips=[];let m;while((m=r.exec(text))!==null)chips.push(m[1].trim());const clean=text.replace(r,"").replace(/\s{2,}/g," ").trim();return{cleanText:clean,chips}}
function formatBotHtml(text){let h=escapeHtml(text);h=h.replace(/\*\*(.+?)\*\*/g,"<strong>$1</strong>");h=h.replace(/\n/g,"<br>");return h}

function injectStyles(){
if(document.getElementById("sia-widget-styles"))return;
const style=document.createElement("style");
style.id="sia-widget-styles";
style.textContent=`
:root{--sia-primary:${PRIMARY_COLOR};--sia-secondary:${SECONDARY_COLOR};--sia-gradient:linear-gradient(135deg,${PRIMARY_COLOR} 0%,${SECONDARY_COLOR} 100%);--sia-gradient-hover:linear-gradient(135deg,${SECONDARY_COLOR} 0%,${PRIMARY_COLOR} 100%);--sia-bg-dark:#1a1a2e;--sia-bg-card:#16213e;--sia-text-primary:#f0f0f0;--sia-text-secondary:#a0a0c0;--sia-glass:rgba(255,255,255,0.06);--sia-glass-border:rgba(255,255,255,0.12);--sia-font:'Inter',system-ui,-apple-system,sans-serif;--sia-shadow:0 20px 60px rgba(0,0,0,0.4),0 0 40px rgba(209,28,93,0.15);--sia-shadow-launcher:0 8px 32px rgba(209,28,93,0.4),0 4px 16px rgba(0,0,0,0.3)}
#sia-widget-launcher{position:fixed;bottom:28px;right:28px;z-index:99999;width:64px;height:64px;border-radius:50%;background:var(--sia-gradient);box-shadow:var(--sia-shadow-launcher);display:flex;align-items:center;justify-content:center;cursor:pointer;border:none;outline:none;transition:all 0.4s cubic-bezier(0.34,1.56,0.64,1);overflow:hidden}
#sia-widget-launcher::before{content:'';position:absolute;inset:0;border-radius:50%;background:var(--sia-gradient-hover);opacity:0;transition:opacity .3s ease}
#sia-widget-launcher:hover::before{opacity:1}
#sia-widget-launcher:hover{transform:scale(1.12) rotate(5deg);box-shadow:0 12px 40px rgba(209,28,93,0.5),0 0 60px rgba(125,51,132,0.3)}
#sia-widget-launcher:active{transform:scale(0.92)}
#sia-widget-launcher::after{content:'';position:absolute;inset:-4px;border-radius:50%;border:2px solid ${PRIMARY_COLOR};opacity:0;animation:sia-ring-idle 3s ease-in-out infinite}
@keyframes sia-ring-idle{0%,100%{transform:scale(1);opacity:0}50%{transform:scale(1.15);opacity:0.4}}
#sia-widget-launcher.open::after{animation:none;opacity:0}
.sia-launcher-icon{position:relative;z-index:2;width:28px;height:28px;fill:white;transition:transform .5s cubic-bezier(0.34,1.56,0.64,1),opacity .3s ease}
#sia-widget-launcher.open .sia-launcher-icon{transform:rotate(180deg) scale(0);opacity:0}
.sia-launcher-close{position:absolute;z-index:2;width:24px;height:24px;fill:white;transition:transform .5s cubic-bezier(0.34,1.56,0.64,1),opacity .3s ease;transform:rotate(-180deg) scale(0);opacity:0}
#sia-widget-launcher.open .sia-launcher-close{transform:rotate(0deg) scale(1);opacity:1}
#sia-widget-launcher.pulse{animation:sia-pulse 2s ease-in-out infinite}
@keyframes sia-pulse{0%,100%{box-shadow:var(--sia-shadow-launcher)}50%{box-shadow:0 0 0 14px ${PRIMARY_COLOR}22,0 0 0 28px ${PRIMARY_COLOR}11,var(--sia-shadow-launcher)}}
.sia-notif-dot{position:absolute;top:2px;right:2px;z-index:3;width:14px;height:14px;border-radius:50%;background:#22c55e;border:2.5px solid #1a1a2e;animation:sia-dot-pulse 2s ease-in-out infinite}
@keyframes sia-dot-pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.2)}}
#sia-widget-launcher.open .sia-notif-dot{display:none}
#sia-widget-window{position:fixed;bottom:104px;right:28px;z-index:99999;width:400px;max-height:600px;height:600px;background:var(--sia-bg-dark);border-radius:20px;box-shadow:var(--sia-shadow);display:flex;flex-direction:column;overflow:hidden;font-family:var(--sia-font);border:1px solid var(--sia-glass-border);opacity:0;transform:translateY(24px) scale(0.92);pointer-events:none;transition:opacity .45s cubic-bezier(0.34,1.56,0.64,1),transform .45s cubic-bezier(0.34,1.56,0.64,1)}
#sia-widget-window.open{opacity:1;transform:translateY(0) scale(1);pointer-events:auto}
#sia-widget-window.closing{opacity:0;transform:translateY(16px) scale(0.95);pointer-events:none;transition:opacity .3s ease,transform .3s ease}
#sia-widget-header{background:var(--sia-gradient);padding:18px 20px;display:flex;align-items:center;gap:14px;color:white;flex-shrink:0;position:relative;overflow:hidden}
#sia-widget-header::before{content:'';position:absolute;top:0;left:-100%;width:100%;height:100%;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.08),transparent);animation:sia-header-shimmer 4s ease-in-out infinite}
@keyframes sia-header-shimmer{0%{left:-100%}50%{left:100%}100%{left:100%}}
#sia-widget-avatar{width:44px;height:44px;border-radius:14px;background:rgba(255,255,255,0.18);backdrop-filter:blur(8px);display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:800;color:white;flex-shrink:0;position:relative;z-index:1;border:1px solid rgba(255,255,255,0.2);transition:transform .3s ease}
#sia-widget-avatar:hover{transform:rotate(10deg) scale(1.1)}
#sia-widget-header-info{position:relative;z-index:1}
#sia-widget-header-info h3{margin:0;font-size:15px;font-weight:700;line-height:1.3;letter-spacing:.3px}
#sia-widget-header-info .sia-subline{display:flex;align-items:center;gap:6px;margin:3px 0 0;font-size:12px;opacity:.9;line-height:1.2;font-weight:400}
.sia-online-dot{width:7px;height:7px;border-radius:50%;background:#22c55e;display:inline-block;animation:sia-online-blink 2.5s ease-in-out infinite}
@keyframes sia-online-blink{0%,100%{opacity:1}50%{opacity:.4}}
#sia-widget-close{margin-left:auto;background:rgba(255,255,255,0.12);border:none;color:white;width:32px;height:32px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;cursor:pointer;line-height:1;transition:all .25s ease;position:relative;z-index:1}
#sia-widget-close:hover{background:rgba(255,255,255,0.25);transform:rotate(90deg)}
#sia-widget-messages{flex:1;overflow-y:auto;padding:18px 16px;display:flex;flex-direction:column;gap:8px;background:var(--sia-bg-dark);scroll-behavior:smooth}
#sia-widget-messages::-webkit-scrollbar{width:4px}
#sia-widget-messages::-webkit-scrollbar-track{background:transparent}
#sia-widget-messages::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.15);border-radius:4px}
.sia-msg{max-width:82%;padding:12px 16px;border-radius:16px;font-size:14px;line-height:1.6;word-wrap:break-word;position:relative;font-weight:400;letter-spacing:.1px}
.sia-msg.bot{align-self:flex-start;background:var(--sia-glass);color:var(--sia-text-primary);border:1px solid var(--sia-glass-border);border-bottom-left-radius:4px;backdrop-filter:blur(8px);animation:sia-msg-bot-in .4s cubic-bezier(0.34,1.56,0.64,1) forwards;opacity:0}
@keyframes sia-msg-bot-in{from{opacity:0;transform:translateX(-12px) scale(0.95)}to{opacity:1;transform:translateX(0) scale(1)}}
.sia-msg.user{align-self:flex-end;background:var(--sia-gradient);color:white;border-bottom-right-radius:4px;font-weight:500;box-shadow:0 4px 16px rgba(209,28,93,0.25);animation:sia-msg-user-in .35s cubic-bezier(0.34,1.56,0.64,1) forwards;opacity:0}
@keyframes sia-msg-user-in{from{opacity:0;transform:translateX(12px) scale(0.95)}to{opacity:1;transform:translateX(0) scale(1)}}
.sia-msg.rendered{animation:none;opacity:1}
.sia-typewriter-cursor{display:inline-block;width:2px;height:16px;background:${PRIMARY_COLOR};margin-left:2px;vertical-align:text-bottom;animation:sia-cursor-blink .7s ease-in-out infinite}
@keyframes sia-cursor-blink{0%,100%{opacity:1}50%{opacity:0}}
.sia-typing{align-self:flex-start;display:flex;gap:5px;padding:14px 18px;background:var(--sia-glass);border:1px solid var(--sia-glass-border);border-radius:16px;border-bottom-left-radius:4px;backdrop-filter:blur(8px);animation:sia-msg-bot-in .3s ease forwards;opacity:0}
.sia-typing-dot{width:8px;height:8px;border-radius:50%;background:var(--sia-text-secondary);animation:sia-wave 1.4s ease-in-out infinite}
.sia-typing-dot:nth-child(2){animation-delay:.15s}
.sia-typing-dot:nth-child(3){animation-delay:.3s}
@keyframes sia-wave{0%,60%,100%{transform:translateY(0);opacity:.4}30%{transform:translateY(-8px);opacity:1}}
.sia-chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:6px;align-self:flex-start;max-width:92%;animation:sia-chips-in .5s cubic-bezier(0.34,1.56,0.64,1) forwards;opacity:0}
@keyframes sia-chips-in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.sia-chip{background:transparent;border:1.5px solid rgba(209,28,93,0.5);color:#f0a0c0;padding:8px 16px;border-radius:24px;font-size:13px;font-weight:500;cursor:pointer;white-space:nowrap;font-family:var(--sia-font);line-height:1.3;transition:all .3s cubic-bezier(0.34,1.56,0.64,1);position:relative;overflow:hidden}
.sia-chip::before{content:'';position:absolute;inset:0;background:var(--sia-gradient);opacity:0;transition:opacity .3s ease;border-radius:24px}
.sia-chip:hover::before{opacity:1}
.sia-chip:hover{color:white;border-color:transparent;transform:translateY(-2px) scale(1.04);box-shadow:0 6px 20px rgba(209,28,93,0.35)}
.sia-chip span{position:relative;z-index:1}
.sia-chip:active{transform:scale(0.95)}
.sia-chip:nth-child(1){animation:sia-chip-pop .4s .1s cubic-bezier(0.34,1.56,0.64,1) forwards;opacity:0}
.sia-chip:nth-child(2){animation:sia-chip-pop .4s .2s cubic-bezier(0.34,1.56,0.64,1) forwards;opacity:0}
.sia-chip:nth-child(3){animation:sia-chip-pop .4s .3s cubic-bezier(0.34,1.56,0.64,1) forwards;opacity:0}
.sia-chip:nth-child(4){animation:sia-chip-pop .4s .4s cubic-bezier(0.34,1.56,0.64,1) forwards;opacity:0}
@keyframes sia-chip-pop{from{opacity:0;transform:scale(0.6) translateY(8px)}to{opacity:1;transform:scale(1) translateY(0)}}
#sia-widget-input-area{padding:14px 16px;border-top:1px solid var(--sia-glass-border);display:flex;gap:10px;align-items:center;background:rgba(22,33,62,0.95);backdrop-filter:blur(10px);flex-shrink:0}
#sia-widget-input{flex:1;border:1.5px solid var(--sia-glass-border);border-radius:28px;padding:12px 20px;font-size:14px;outline:none;font-family:var(--sia-font);font-weight:400;background:var(--sia-glass);color:var(--sia-text-primary);transition:all .3s ease;letter-spacing:.2px}
#sia-widget-input:focus{border-color:${PRIMARY_COLOR};background:rgba(255,255,255,0.08);box-shadow:0 0 0 3px ${PRIMARY_COLOR}22}
#sia-widget-input::placeholder{color:var(--sia-text-secondary)}
#sia-widget-send{width:42px;height:42px;border-radius:50%;border:none;background:var(--sia-gradient);color:white;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .3s cubic-bezier(0.34,1.56,0.64,1);flex-shrink:0;box-shadow:0 4px 12px rgba(209,28,93,0.3)}
#sia-widget-send:hover{transform:scale(1.1) rotate(15deg);box-shadow:0 6px 20px rgba(209,28,93,0.45)}
#sia-widget-send:active{transform:scale(0.9)}
#sia-widget-send svg{width:18px;height:18px;fill:white;position:relative;z-index:1}
#sia-widget-powered{text-align:center;padding:8px;font-size:11px;color:var(--sia-text-secondary);background:rgba(22,33,62,0.95);flex-shrink:0;letter-spacing:.3px;font-weight:400}
#sia-widget-powered a{color:${PRIMARY_COLOR};text-decoration:none;font-weight:600;transition:color .2s ease}
#sia-widget-powered a:hover{color:${SECONDARY_COLOR}}
.sia-particles{position:absolute;inset:0;overflow:hidden;pointer-events:none}
.sia-particle{position:absolute;width:4px;height:4px;background:rgba(255,255,255,0.15);border-radius:50%;animation:sia-float 6s ease-in-out infinite}
.sia-particle:nth-child(1){top:20%;left:10%;animation-delay:0s;animation-duration:5s}
.sia-particle:nth-child(2){top:60%;left:80%;animation-delay:1s;animation-duration:7s}
.sia-particle:nth-child(3){top:40%;left:50%;animation-delay:2s;animation-duration:6s}
.sia-particle:nth-child(4){top:80%;left:30%;animation-delay:.5s;animation-duration:8s}
.sia-particle:nth-child(5){top:10%;left:70%;animation-delay:1.5s;animation-duration:5.5s}
@keyframes sia-float{0%,100%{transform:translateY(0) translateX(0);opacity:.3}25%{transform:translateY(-8px) translateX(4px);opacity:.6}50%{transform:translateY(-4px) translateX(-3px);opacity:.4}75%{transform:translateY(-10px) translateX(2px);opacity:.5}}
.sia-welcome-overlay{position:absolute;inset:0;z-index:10;background:var(--sia-gradient);display:flex;flex-direction:column;align-items:center;justify-content:center;animation:sia-welcome-fade .8s 1.5s ease forwards;opacity:1;pointer-events:none}
@keyframes sia-welcome-fade{to{opacity:0}}
.sia-welcome-logo{font-size:48px;font-weight:800;color:white;animation:sia-welcome-pop .6s cubic-bezier(0.34,1.56,0.64,1)}
.sia-welcome-text{font-size:14px;color:rgba(255,255,255,0.8);margin-top:8px;font-weight:400;animation:sia-welcome-pop .6s .2s cubic-bezier(0.34,1.56,0.64,1) both}
@keyframes sia-welcome-pop{from{opacity:0;transform:scale(0.5)}to{opacity:1;transform:scale(1)}}
@media(max-width:480px){#sia-widget-window{width:calc(100vw - 16px);right:8px;bottom:88px;max-height:calc(100vh - 108px);height:calc(100vh - 108px);border-radius:16px}#sia-widget-launcher{bottom:18px;right:18px;width:58px;height:58px}}
`;
document.head.appendChild(style);
}

function buildWidget(){
const launcher=document.createElement("button");
launcher.id="sia-widget-launcher";
launcher.setAttribute("aria-label","Chat with Sia");
launcher.innerHTML=`<svg class="sia-launcher-icon" viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/><path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg><svg class="sia-launcher-close" viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg><div class="sia-notif-dot"></div>`;
launcher.onclick=toggleWidget;
document.body.appendChild(launcher);

const win=document.createElement("div");
win.id="sia-widget-window";
win.innerHTML=`<div id="sia-widget-header"><div class="sia-particles"><div class="sia-particle"></div><div class="sia-particle"></div><div class="sia-particle"></div><div class="sia-particle"></div><div class="sia-particle"></div></div><div id="sia-widget-avatar">✦</div><div id="sia-widget-header-info"><h3>${BOT_NAME} — SSSi Assistant</h3><div class="sia-subline"><span class="sia-online-dot"></span><span>Online • Replies instantly</span></div></div><button id="sia-widget-close" aria-label="Close chat">&times;</button></div><div id="sia-widget-messages"></div><div id="sia-widget-input-area"><input id="sia-widget-input" type="text" placeholder="Type your message..." autocomplete="off" maxlength="500"><button id="sia-widget-send" aria-label="Send message"><svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg></button></div><div id="sia-widget-powered">Powered by <a href="https://sssi.in" target="_blank" rel="noopener">SSSi.in</a></div>`;
document.body.appendChild(win);

document.getElementById("sia-widget-close").onclick=toggleWidget;
document.getElementById("sia-widget-send").onclick=()=>handleSend();
document.getElementById("sia-widget-input").addEventListener("keydown",(e)=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();handleSend()}});
startPulse();
}

let firstOpen=true;
function toggleWidget(){
const win=document.getElementById("sia-widget-window");
const launcher=document.getElementById("sia-widget-launcher");
if(!widgetOpen){
widgetOpen=true;
launcher.classList.add("open");
win.classList.remove("closing");
if(firstOpen){firstOpen=false;const ov=document.createElement("div");ov.className="sia-welcome-overlay";ov.innerHTML=`<div class="sia-welcome-logo">✦</div><div class="sia-welcome-text">${BOT_NAME} is ready to help</div>`;win.appendChild(ov);setTimeout(()=>ov.remove(),2500)}
requestAnimationFrame(()=>win.classList.add("open"));
launcher.classList.remove("pulse");stopPulse();
if(messages.length===0)setTimeout(()=>showWelcomeMessage(),600);
else renderAllMessages();
const input=document.getElementById("sia-widget-input");
setTimeout(()=>input&&input.focus(),500);
resetInactivityTimer();
}else{
widgetOpen=false;
launcher.classList.remove("open");
win.classList.remove("open");
win.classList.add("closing");
clearInactivityTimer();
setTimeout(()=>win.classList.remove("closing"),350);
}}

function showWelcomeMessage(){
const tod=getTimeOfDay();
let greeting,chips;
if(tod==="morning"){greeting=`🌅 Good morning! I'm ${BOT_NAME}, your SSSi learning assistant. Ready to find your perfect tutor? It takes under 30 seconds!`;chips=["🔍 Find a Tutor","📅 Book Free Trial","💰 Pricing","📞 Talk to Counselor"]}
else if(tod==="afternoon"){greeting=`👋 Hi! I'm ${BOT_NAME}, your SSSi learning assistant. I can book a FREE demo class for you in under 30 seconds!`;chips=["🔍 Find a Tutor","📅 Book Free Trial","💰 Pricing","📞 Talk to Counselor"]}
else{greeting=`🌙 Good evening! I'm ${BOT_NAME} from SSSi. Perfect time to plan your learning — want to book a free demo?`;chips=["🔍 Find a Tutor","📅 Book Free Trial","💰 Pricing","📞 Talk to Counselor"]}
addBotMessage(greeting,chips,true);
}

function addBotMessage(text,chips,useTypewriter){
messages.push({role:"bot",text,chips:chips||[]});persistState();
if(useTypewriter&&!isTypewriting)renderMessageWithTypewriter({role:"bot",text,chips:chips||[]});
else renderMessage({role:"bot",text,chips:chips||[]});
scrollToBottom();
}

function addUserMessage(text){messages.push({role:"user",text});persistState();renderMessage({role:"user",text});scrollToBottom()}

function renderMessage(msg,skipAnim){
const c=document.getElementById("sia-widget-messages");if(!c)return;
if(msg.role==="user"){const d=document.createElement("div");d.className="sia-msg user"+(skipAnim?" rendered":"");d.textContent=msg.text;c.appendChild(d)}
else{const d=document.createElement("div");d.className="sia-msg bot"+(skipAnim?" rendered":"");d.innerHTML=formatBotHtml(msg.text);c.appendChild(d);
if(msg.chips&&msg.chips.length>0)renderChips(msg.chips,c,skipAnim)}
}

function renderChips(chips,container,skipAnim){
const cc=document.createElement("div");cc.className="sia-chips"+(skipAnim?" rendered":"");
if(skipAnim)cc.style.opacity="1";
chips.forEach(label=>{const b=document.createElement("button");b.className="sia-chip";b.innerHTML=`<span>${escapeHtml(label)}</span>`;if(skipAnim){b.style.opacity="1";b.style.animation="none"}b.onclick=()=>handleChipClick(label);cc.appendChild(b)});
container.appendChild(cc);
}

function renderMessageWithTypewriter(msg){
const c=document.getElementById("sia-widget-messages");if(!c)return;
isTypewriting=true;
const d=document.createElement("div");d.className="sia-msg bot";d.innerHTML='<span class="sia-typewriter-cursor"></span>';c.appendChild(d);scrollToBottom();
const fullText=msg.text;let i=0;
function typeNext(){
if(i<fullText.length){d.innerHTML=formatBotHtml(fullText.substring(0,i+1))+'<span class="sia-typewriter-cursor"></span>';i++;scrollToBottom();
let delay=TYPEWRITER_CHAR_MS;const ch=fullText[i-1];if(ch==='.'||ch==='!'||ch==='?')delay=120;else if(ch===',')delay=60;else if(ch===' ')delay=10;
setTimeout(typeNext,delay)}
else{d.innerHTML=formatBotHtml(fullText);isTypewriting=false;
if(msg.chips&&msg.chips.length>0)setTimeout(()=>{renderChips(msg.chips,c,false);scrollToBottom()},200)}}
setTimeout(typeNext,300);
}

function renderAllMessages(){const c=document.getElementById("sia-widget-messages");if(!c)return;c.innerHTML="";messages.forEach(m=>renderMessage(m,true));scrollToBottom()}
function scrollToBottom(){const c=document.getElementById("sia-widget-messages");if(c)setTimeout(()=>c.scrollTop=c.scrollHeight,50)}

function showTyping(){if(isTyping)return;isTyping=true;const c=document.getElementById("sia-widget-messages");if(!c)return;const t=document.createElement("div");t.className="sia-typing";t.id="sia-typing-indicator";t.innerHTML=`<div class="sia-typing-dot"></div><div class="sia-typing-dot"></div><div class="sia-typing-dot"></div>`;c.appendChild(t);scrollToBottom()}
function hideTyping(){isTyping=false;const e=document.getElementById("sia-typing-indicator");if(e)e.remove()}

function handleChipClick(label){
document.querySelectorAll(".sia-chips").forEach(c=>{const last=document.getElementById("sia-widget-messages").lastElementChild;if(c===last||c===last?.previousElementSibling){c.querySelectorAll(".sia-chip").forEach(b=>{b.disabled=true;b.style.opacity="0.35";b.style.cursor="default";b.style.pointerEvents="none"})}});
handleSend(label);
}

function extractStateFromResponse(botText,userText){
const lower=(userText||"").toLowerCase();
if(/class\s*1[\s\-]5|class [1-5]\b/i.test(lower))sessionState.grade="Class 1-5";
else if(/class\s*6[\s\-]8|class [6-8]\b/i.test(lower))sessionState.grade="Class 6-8";
else if(/class\s*9[\s\-]10|class (9|10)\b|10th/i.test(lower))sessionState.grade="Class 9-10";
else if(/class\s*11[\s\-]12|class (11|12)\b|11th|12th/i.test(lower))sessionState.grade="Class 11-12";
if(/\bcbse\b/i.test(lower))sessionState.board="CBSE";
else if(/\bicse\b/i.test(lower))sessionState.board="ICSE";
const subjectMap={maths:"Maths",physics:"Physics",chemistry:"Chemistry",biology:"Biology",english:"English"};
Object.entries(subjectMap).forEach(([kw,name])=>{if(lower.includes(kw)&&!sessionState.subjects.includes(name))sessionState.subjects.push(name)});
if(!sessionState.name&&/^[A-Z][a-z]{1,20}(\s+[A-Z][a-z]{1,20})?$/.test(userText.trim())){const lastBot=messages.filter(m=>m.role==="bot").slice(-1)[0];if(lastBot&&/what('s| is) your name/i.test(lastBot.text))sessionState.name=userText.trim()}
const phoneMatch=lower.match(/(?:\+?91[\s-]?)?([6-9]\d{9})/);
if(phoneMatch&&!sessionState.phone)sessionState.phone=phoneMatch[1];
const lang=detectLanguage(userText);if(lang!=="English")sessionState.language=lang;
persistState();
}

function attemptLeadCapture(){
if(sessionState.lead_captured||!sessionState.name||!sessionState.phone)return;
sessionState.lead_captured=true;persistState();
fetch(API_BASE+"/api/v1/chatbot/capture-lead",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({tenant_id:ORG_ID,visitor_id:visitorId,name:sessionState.name,phone:sessionState.phone,grade:sessionState.grade,board:sessionState.board,subjects:sessionState.subjects,goal:sessionState.goal})}).then(r=>r.json()).then(d=>console.log("[Sia] Lead captured:",d)).catch(e=>{console.warn("[Sia] Lead capture failed:",e);sessionState.lead_captured=false;persistState()});
}

async function handleSend(overrideText){
const input=document.getElementById("sia-widget-input");
const text=(overrideText||(input&&input.value)||"").trim();
if(!text||isTyping)return;
if(input)input.value="";
addUserMessage(text);extractStateFromResponse("",text);showTyping();resetInactivityTimer();
try{
const res=await fetch(API_BASE+"/api/v1/chatbot/message",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({tenant_id:ORG_ID,visitor_id:visitorId,message:text,session_state:sessionState})});
const data=await res.json();
const botResponse=data.response||data.message||"I'm having trouble — please try again!";
await new Promise(r=>setTimeout(r,randomDelay()));hideTyping();
const{cleanText,chips}=parseChips(botResponse);
addBotMessage(cleanText||botResponse,chips,true);
extractStateFromResponse(botResponse,text);attemptLeadCapture();
}catch(err){console.error("[Sia] API error:",err);hideTyping();addBotMessage("Oops — something went wrong! Please try again or reach us at sssi.in 📞",[],false)}
}

function resetInactivityTimer(){clearInactivityTimer();inactivityTimer=setTimeout(()=>{if(widgetOpen&&!isTyping)addBotMessage("Still there? No rush — just tap any option below when you're ready! 😊",["📅 Book Free Demo","💰 Pricing","📞 Talk to Counselor"],true)},INACTIVITY_TIMEOUT_MS)}
function clearInactivityTimer(){if(inactivityTimer){clearTimeout(inactivityTimer);inactivityTimer=null}}
function startPulse(){if(widgetOpen)return;pulseTimer=setInterval(()=>{const l=document.getElementById("sia-widget-launcher");if(l&&!widgetOpen){l.classList.add("pulse");setTimeout(()=>l.classList.remove("pulse"),3000)}},ATTENTION_PULSE_MS)}
function stopPulse(){if(pulseTimer){clearInterval(pulseTimer);pulseTimer=null}}

injectStyles();buildWidget();
console.log("%c✅ Sia Widget v3.0 injected successfully!","color:#22c55e;font-size:16px;font-weight:bold");
console.log("%cClick the crimson button in the bottom-right corner 👇","color:#f0a0c0;font-size:13px");
})();
