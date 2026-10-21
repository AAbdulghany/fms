#!/usr/bin/env bash
# Bootstrap Ubuntu 22.04/24.04 VM for the Orbit pilot stack (Docker Compose).
# Run as root or with sudo: bash deploy/pilot/setup-ubuntu.sh

set -euo pipefail

echo "==> Installing Docker..."
if ! command -v docker >/dev/null 2>&1; then
  apt-get update
  apt-get install -y ca-certificates curl
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "${VERSION_CODENAME}") stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
fi

echo "==> Docker version:"
docker compose version

echo "==> Opening firewall (ufw) for HTTP if active..."
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
  ufw allow 80/tcp || true
  ufw allow 443/tcp || true
  ufw allow "${WEB_PORT:-8080}/tcp" || true
fi

echo "==> Done. Next steps:"
echo "  1. Clone repo branch pilot/live"
echo "  2. cp deploy/pilot/.env.example deploy/pilot/.env && chmod 600 deploy/pilot/.env && nano deploy/pilot/.env"
echo "  3. docker compose -f docker-compose-pilot.yml -f deploy/pilot/docker-compose.live.yml --env-file deploy/pilot/.env up -d --build"
echo "  4. HTTPS: Cloudflare Tunnel -> http://localhost:\${WEB_PORT} — see docs/guides/pilot-stack.md"
