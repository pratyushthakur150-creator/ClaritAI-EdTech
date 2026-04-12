# Quick Start Guide - Fix Timeout Issues

## Problem: Frontend timeout when calling backend

The backend server is not running or is hanging on startup (likely Redis connection).

## Solution: Start Backend Properly

### Option 1: Use the startup script (Recommended)

```powershell
cd "C:\Users\praty\OneDrive\Desktop\Edtech admission Final\ravian-backend\ravian-backend\ravian-backend"
.\START_BACKEND.ps1
```

### Option 2: Manual start

```powershell
cd "C:\Users\praty\OneDrive\Desktop\Edtech admission Final\ravian-backend\ravian-backend\ravian-backend"
.\venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## What to Look For

When the backend starts, you should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Starting up Ravian Backend API...
INFO:     ⚠ Redis connection failed (will continue without Redis): ...
INFO:     ✓ Application startup completed successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Important:** Even if Redis fails, the server should still start. The warning about Redis is OK - rate limiting will be disabled but the API will work.

## Verify Backend is Running

Open a new PowerShell window and run:

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing
```

You should get a 200 response with JSON.

## If Backend Still Hangs

1. **Check if Redis is running** (optional - backend works without it):
   ```powershell
   # Check if Redis is running on port 6379
   Test-NetConnection -ComputerName localhost -Port 6379
   ```

2. **Check database connection** - Make sure PostgreSQL is running and `.env` has correct DB settings:
   - DB_HOST=localhost
   - DB_PORT=5433
   - DB_USER=postgres
   - DB_PASSWORD=ClaritAI
   - DB_NAME=ravian_dev

3. **Check backend logs** - Look at the terminal where you started the backend for error messages.

## Once Backend is Running

1. **Test registration in Swagger**: http://127.0.0.1:8000/docs
   - Try POST /api/v1/auth/register

2. **Test from frontend**: http://localhost:3000/register
   - Should now work without timeout!

## Common Issues

- **Backend not running**: Start it using the commands above
- **Database connection error**: Check PostgreSQL is running and `.env` settings are correct
- **Redis timeout**: This is OK - backend will continue without Redis
- **Port 8000 already in use**: Stop any other process using port 8000 or change the port
