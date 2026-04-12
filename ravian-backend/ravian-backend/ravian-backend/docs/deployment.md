# Ravian — Production Deployment Guide

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Vercel          │     │  Railway          │     │  External     │
│                  │     │                   │     │               │
│  Next.js App     │────▶│  FastAPI Backend  │────▶│  OpenAI API   │
│  (Dashboard)     │     │  (Python 3.11)    │     │  VAPI          │
│                  │     │                   │     │  Twilio        │
│  widget.js       │     │  PostgreSQL       │     │  Google Cal    │
│  (Embeddable)    │     │  Redis            │     └──────────────┘
└─────────────────┘     │  ChromaDB (local) │
                        └──────────────────┘
```

---

## Prerequisites

- [Node.js 18+](https://nodejs.org/)
- [Python 3.11+](https://python.org/)
- [Railway CLI](https://docs.railway.app/develop/cli)
- [Vercel CLI](https://vercel.com/docs/cli)
- A PostgreSQL database (Railway provides one)
- A Redis instance (Railway provides one)
- API keys: OpenAI, VAPI, Google Calendar, optionally Twilio

---

## 1. Backend Deployment (Railway)

### 1.1 Install Railway CLI

```bash
npm install -g @railway/cli
railway login
```

### 1.2 Initialize Project

```bash
# Navigate to the backend root
cd ravian-backend/ravian-backend/ravian-backend

# Initialize Railway project
railway init
```

### 1.3 Add Database Plugins

In the **Railway Dashboard** (https://railway.app):
1. Open your project
2. Click **"+ New"** → **PostgreSQL** — this auto-injects `DATABASE_URL`
3. Click **"+ New"** → **Redis** — this auto-injects `REDIS_URL`

### 1.4 Configure Environment Variables

In Railway Dashboard → your service → **Variables**, add:

| Variable | Value |
|----------|-------|
| `OPENAI_API_KEY` | `sk-...` |
| `CHATBOT_API_KEY` | `sk-...` |
| `JWT_SECRET_KEY` | Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `VAPI_API_KEY` | From VAPI dashboard |
| `VAPI_ASSISTANT_ID` | From VAPI dashboard |
| `VAPI_PHONE_NUMBER_ID` | From VAPI dashboard |
| `GROQ_API_KEY` | From Groq console |
| `CORS_ORIGINS` | `https://ravian.vercel.app,https://ravian.ai` |
| `DEBUG` | `false` |
| `LOG_LEVEL` | `INFO` |

> **Note:** `DATABASE_URL` and `REDIS_URL` are auto-injected by Railway plugins.
> However, Ravian uses individual `DB_*` and `REDIS_*` variables. You may need to
> parse them or add: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`,
> `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` from the injected URLs.

### 1.5 Deploy

```bash
railway up
```

### 1.6 Run Database Migrations

```bash
railway run alembic upgrade head
```

### 1.7 Get Your Backend URL

```bash
railway domain
# → ravian-backend-production.railway.app
```

### 1.8 Verify Backend

```bash
curl https://ravian-backend-production.railway.app/health
# Should return: {"status": "ok", ...}
```

---

## 2. Frontend Deployment (Vercel)

### 2.1 Install Vercel CLI

```bash
npm install -g vercel
```

### 2.2 Deploy

```bash
cd ravian-backend/ravian-backend/ravian-frontend

vercel deploy --prod
```

### 2.3 Set Environment Variables

In the **Vercel Dashboard** → Project Settings → Environment Variables:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://ravian-backend-production.railway.app` |
| `NEXT_PUBLIC_API_BASE_URL` | `https://ravian-backend-production.railway.app/api/v1` |
| `NEXT_PUBLIC_VAPI_ASSISTANT_ID` | Your VAPI assistant ID |

### 2.4 Redeploy with Environment Variables

```bash
vercel deploy --prod
```

### 2.5 Verify Frontend

- Dashboard: `https://ravian.vercel.app` → should show login page
- Widget: `https://ravian.vercel.app/widget.js` → should return JavaScript

---

## 3. Create First Pilot Client

### 3.1 Create Tenant via API

```bash
curl -X POST https://ravian-backend-production.railway.app/api/v1/leads/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "org_name": "Company X",
    "domain": "companyx.com",
    "chatbot_name": "Aria",
    "tone": "friendly and professional",
    "primary_color": "#2D6A4F",
    "plan": "pilot"
  }'
```

### 3.2 Get Widget Snippet

The API response includes a widget snippet. Send this to the client:

```html
<!-- Paste before </body> on companyx.com -->
<script>
  (function(){
    var s = document.createElement('script');
    s.src = 'https://ravian.vercel.app/widget.js';
    s.setAttribute('data-org', 'company-x');
    s.setAttribute('data-color', '#2D6A4F');
    s.setAttribute('data-name', 'Aria');
    document.body.appendChild(s);
  })();
</script>
```

### 3.3 Create CRM User Accounts

```bash
curl -X POST https://ravian-backend-production.railway.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@companyx.com",
    "password": "SecurePassword123!",
    "full_name": "Admin User",
    "role": "admin",
    "tenant_id": "company-x"
  }'
```

### 3.4 Index Content into ChromaDB

Upload the client's FAQ, syllabus, and fee documents via the content API:

```bash
curl -X POST https://ravian-backend-production.railway.app/api/v1/content/upload \
  -F "file=@companyx-faq.pdf" \
  -F "tenant_id=company-x" \
  -F "doc_type=faq"
```

---

## 4. Validation Checklist

### Backend
- [ ] `GET /health` → `{"status": "ok"}`
- [ ] `POST /api/v1/auth/login` → returns JWT
- [ ] `POST /api/v1/chatbot/message` → returns GPT reply
- [ ] `GET /api/v1/leads` → returns lead list
- [ ] `GET /api/v1/calls` → returns call logs

### Frontend
- [ ] Dashboard loads at production URL
- [ ] Login works with test credentials
- [ ] Lead table displays correctly
- [ ] Widget.js is accessible with CORS headers

### Pilot Client
- [ ] Tenant created in database
- [ ] CORS allows client domain
- [ ] Widget loads on client's test page
- [ ] Test chat creates lead in CRM
- [ ] Content indexed in ChromaDB for RAG

---

## 5. Common Issues

### CORS Errors
- Ensure `CORS_ORIGINS` includes the client's domain
- Check `vercel.json` has `Access-Control-Allow-Origin: *` for widget.js

### Database Connection
- Railway auto-injects `DATABASE_URL` but Ravian uses individual `DB_*` vars
- Parse the URL and set each variable manually in Railway dashboard

### Redis Not Available
- The backend gracefully falls back to MockRedis if Redis is unavailable
- For production, always use a real Redis instance

### ChromaDB
- ChromaDB runs locally inside the Railway container
- Data persists in `/app/chroma_db` but will be lost on redeploy
- For production, consider a persistent volume or external ChromaDB service
