Write-Host "Starting Ala-Too PM..." -ForegroundColor Cyan

$job = Start-Job {
    & cloudflared tunnel --url http://localhost:9000 2>&1
}

Write-Host "Getting public URL..." -ForegroundColor Yellow

$url = $null
$attempts = 0
while (-not $url -and $attempts -lt 30) {
    Start-Sleep -Seconds 1
    $output = Receive-Job $job -Keep 2>&1 | Out-String
    if ($output -match 'https://[a-z0-9\-]+\.trycloudflare\.com') {
        $url = $matches[0]
    }
    $attempts++
}

if (-not $url) {
    Write-Host "Failed to get URL. Check cloudflared." -ForegroundColor Red
    exit 1
}

$domain = $url -replace 'https://', ''
Write-Host "URL: $url" -ForegroundColor Green

$env_content = Get-Content .env -Raw
$env_content = $env_content -replace 'TAIGA_SCHEME=\S*', 'TAIGA_SCHEME=https'
$env_content = $env_content -replace 'TAIGA_DOMAIN=\S*', "TAIGA_DOMAIN=$domain"
$env_content = $env_content -replace 'TAIGA_WS_SCHEME=\S*', 'TAIGA_WS_SCHEME=wss'
$env_content = $env_content -replace 'COOKIE_SECURE=\S*', 'COOKIE_SECURE=True'
Set-Content .env $env_content -Encoding UTF8
Write-Host ".env updated" -ForegroundColor Green

Write-Host "Starting Docker containers..." -ForegroundColor Yellow
docker compose up -d

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Ala-Too PM is running!" -ForegroundColor Green
Write-Host "  URL: $url" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Keep this window open. Press Ctrl+C to stop." -ForegroundColor Yellow

Wait-Job $job
