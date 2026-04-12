# ═══════════════════════════════════════════════════════════════
# Ravian — Deployment Validation Script
# Run this after deploying both backend and frontend
# Usage: .\validate_deployment.ps1 [-BackendUrl "https://..."] [-FrontendUrl "https://..."]
# ═══════════════════════════════════════════════════════════════

param(
    [string]$BackendUrl = "http://localhost:8000",
    [string]$FrontendUrl = "http://localhost:3000"
)

$ErrorActionPreference = "Continue"
$pass = 0
$fail = 0
$total = 0

function Test-Endpoint {
    param([string]$Name, [string]$Url, [string]$Method = "GET", [string]$Body = $null)
    
    $script:total++
    Write-Host -NoNewline "  [$script:total] $Name ... "
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            ContentType = "application/json"
            TimeoutSec = 10
            ErrorAction = "Stop"
        }
        if ($Body) { $params.Body = $Body }
        
        $response = Invoke-RestMethod @params
        Write-Host "PASS ✅" -ForegroundColor Green
        $script:pass++
        return $response
    }
    catch {
        $status = $_.Exception.Response.StatusCode.value__
        Write-Host "FAIL ❌ (HTTP $status - $($_.Exception.Message))" -ForegroundColor Red
        $script:fail++
        return $null
    }
}

function Test-UrlAccessible {
    param([string]$Name, [string]$Url)
    
    $script:total++
    Write-Host -NoNewline "  [$script:total] $Name ... "
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 10 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "PASS ✅" -ForegroundColor Green
            $script:pass++
        } else {
            Write-Host "FAIL ❌ (HTTP $($response.StatusCode))" -ForegroundColor Red
            $script:fail++
        }
    }
    catch {
        Write-Host "FAIL ❌ ($($_.Exception.Message))" -ForegroundColor Red
        $script:fail++
    }
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  RAVIAN DEPLOYMENT VALIDATION" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Backend:  $BackendUrl" -ForegroundColor Yellow
Write-Host "  Frontend: $FrontendUrl" -ForegroundColor Yellow
Write-Host ""

# ── Backend Tests ─────────────────────────────────────────────
Write-Host "─── BACKEND ───────────────────────────────────────" -ForegroundColor Cyan

Test-Endpoint "Health check" "$BackendUrl/health"
Test-Endpoint "Root endpoint" "$BackendUrl/"
Test-Endpoint "API docs accessible" "$BackendUrl/docs"
Test-Endpoint "Leads endpoint" "$BackendUrl/api/v1/leads"
Test-Endpoint "Chatbot message" "$BackendUrl/api/v1/chatbot/message" "POST" '{"message":"hello","session_id":"test123","tenant_id":"default","page_url":"https://test.com"}'

Write-Host ""

# ── Frontend Tests ────────────────────────────────────────────
Write-Host "─── FRONTEND ──────────────────────────────────────" -ForegroundColor Cyan

Test-UrlAccessible "Dashboard loads" "$FrontendUrl"
Test-UrlAccessible "Widget.js accessible" "$FrontendUrl/widget.js"

Write-Host ""

# ── Results ───────────────────────────────────────────────────
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  RESULTS: $pass passed, $fail failed, $total total" -ForegroundColor $(if ($fail -eq 0) { "Green" } else { "Red" })
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
