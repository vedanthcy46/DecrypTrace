$ErrorActionPreference = 'SilentlyContinue'

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "  DecrypTrace - Clean Reset" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

# 1. Stop services if they are running
Write-Host "Stopping any running Python processes..."
Get-Process python | Stop-Process -Force

# 2. Delete Databases
Write-Host "Deleting databases..."
Remove-Item -Path "decryptrace.db" -Force
Remove-Item -Path "dlt\node1\ledger.db" -Force
Remove-Item -Path "dlt\node2\ledger.db" -Force
Remove-Item -Path "dlt\node3\ledger.db" -Force

# 3. Delete Keystore
Write-Host "Deleting keystore..."
Remove-Item -Path "recipient-agent\keystore\*" -Recurse -Force

# 4. Delete Stored Files
Write-Host "Deleting stored files..."
Remove-Item -Path "backend\storage\encrypted\*" -Recurse -Force
Remove-Item -Path "backend\storage\decrypted\*" -Recurse -Force
Remove-Item -Path "backend\storage\leaked\*" -Recurse -Force

Write-Host "===========================================" -ForegroundColor Green
Write-Host "  Reset Complete! System is completely clean." -ForegroundColor Green
Write-Host "  You can now run .\scripts\start-all.ps1" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Green
