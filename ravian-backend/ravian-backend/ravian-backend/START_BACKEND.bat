@echo off
cd /d "C:\Users\amans\OneDrive\Desktop\Edtech admission\ravian-backend\ravian-backend"
echo Stopping any existing backend...
taskkill /F /IM python.exe 2>nul
timeout /t 2
echo Starting backend with CORS fix...
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause

