# Expose local Docker demo to a client in ~2 minutes (full stack).
# Prereq: demo running on http://localhost:8080
#
#   docker compose -f docker-compose.yml -f docker-compose.demo.yml up
#
# Then:
#   .\scripts\share-demo-tunnel.ps1
#
# Sends traffic to localhost:8080 (nginx + API + DB in Docker).
# Requires cloudflared: winget install Cloudflare.cloudflared

$ErrorActionPreference = "Stop"

$demoUrl = "http://localhost:8080"
Write-Host "Checking local demo at $demoUrl ..."
try {
    $r = Invoke-WebRequest -Uri "$demoUrl/api/v1/server-time" -UseBasicParsing -TimeoutSec 5
    if ($r.StatusCode -ne 200) { throw "Unexpected status" }
} catch {
    Write-Host "ERROR: Demo not reachable. Start Docker first:" -ForegroundColor Red
    Write-Host "  docker compose -f docker-compose.yml -f docker-compose.demo.yml up"
    exit 1
}

if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    Write-Host "cloudflared not found. Install:" -ForegroundColor Yellow
    Write-Host "  winget install Cloudflare.cloudflared"
    Write-Host "Or download: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
    exit 1
}

Write-Host ""
Write-Host "Starting tunnel -> $demoUrl" -ForegroundColor Green
Write-Host "Copy the https://....trycloudflare.com URL and send to your client."
Write-Host "Keep this window open. Press Ctrl+C to stop."
Write-Host ""
cloudflared tunnel --url $demoUrl
