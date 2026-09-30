<#
.SYNOPSIS
    Start all DecrypTrace services
.DESCRIPTION
    Starts the 3 DLT nodes, the backend API, and the recipient agent
#>

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  DecrypTrace - Starting All Services" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$projectDir = Split-Path -Parent $PSScriptRoot

$env:PYTHONPATH = $projectDir

# Start DLT Nodes
Write-Host "`n[1/5] Starting DLT Node 1 (port 8001)..." -ForegroundColor Blue
Start-Process -NoNewWindow powershell -ArgumentList "-Command", "cd '$projectDir'; `$env:PYTHONPATH='$projectDir'; .\.venv\Scripts\python scripts\run_dlt.py node1 8001" -PassThru | Out-Null
Start-Sleep -Seconds 1

Write-Host "[2/5] Starting DLT Node 2 (port 8002)..." -ForegroundColor Blue
Start-Process -NoNewWindow powershell -ArgumentList "-Command", "cd '$projectDir'; `$env:PYTHONPATH='$projectDir'; .\.venv\Scripts\python scripts\run_dlt.py node2 8002" -PassThru | Out-Null
Start-Sleep -Seconds 1

Write-Host "[3/5] Starting DLT Node 3 (port 8003)..." -ForegroundColor Blue
Start-Process -NoNewWindow powershell -ArgumentList "-Command", "cd '$projectDir'; `$env:PYTHONPATH='$projectDir'; .\.venv\Scripts\python scripts\run_dlt.py node3 8003" -PassThru | Out-Null
Start-Sleep -Seconds 2

# Start Backend
Write-Host "[4/5] Starting Backend API (port 8000)..." -ForegroundColor Green
Start-Process -NoNewWindow powershell -ArgumentList "-Command", "cd '$projectDir'; `$env:PYTHONPATH='$projectDir'; .\.venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000" -PassThru | Out-Null
Start-Sleep -Seconds 2

# Start Recipient Agent
Write-Host "[5/5] Starting Recipient Agent (port 8010)..." -ForegroundColor Yellow
Start-Process -NoNewWindow powershell -ArgumentList "-Command", "cd '$projectDir\recipient-agent'; `$env:PYTHONPATH='$projectDir\recipient-agent'; ..\.venv\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8010" -PassThru | Out-Null
Start-Sleep -Seconds 1

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  All services started!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Services:" -ForegroundColor White
Write-Host "    DLT Node 1:        http://127.0.0.1:8001" -ForegroundColor Blue
Write-Host "    DLT Node 2:        http://127.0.0.1:8002" -ForegroundColor Blue
Write-Host "    DLT Node 3:        http://127.0.0.1:8003" -ForegroundColor Blue
Write-Host "    Backend API:       http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "    API Docs:          http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "    Recipient Agent:   http://127.0.0.1:8010" -ForegroundColor Yellow
Write-Host ""
Write-Host "  To start the frontend:" -ForegroundColor White
Write-Host "    cd frontend && npm run dev" -ForegroundColor Magenta
Write-Host ""
