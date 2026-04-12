# Clear Python cache and restart backend
# Run this if you're getting 403 on content endpoints

$ErrorActionPreference = "Stop"
$backendDir = $PSScriptRoot

Write-Host "Clearing Python __pycache__..." -ForegroundColor Yellow
Get-ChildItem -Path $backendDir -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | 
    Where-Object { $_.FullName -notmatch "\\venv\\" } |
    ForEach-Object {
        Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  Removed: $($_.FullName)"
    }

Write-Host "`nRestart backend with:" -ForegroundColor Green
Write-Host "  cd `"$backendDir`"" -ForegroundColor Cyan
Write-Host "  venv\Scripts\activate" -ForegroundColor Cyan
Write-Host "  uvicorn app.main:app --reload --host 127.0.0.1 --port 8001" -ForegroundColor Cyan
Write-Host "`nVerify new code: GET http://127.0.0.1:8001/api/v1/content/debug" -ForegroundColor Green
Write-Host "  Expected: {`"status`":`"content_router_v2`",`"permission_checks`":`"NONE`"}" -ForegroundColor Gray
