#!/bin/bash
# ==============================================
# DEPLOY NA VPS (Ubuntu 24 / Hetzner)
# Użycie: chmod +x deploy/deploy.sh && ./deploy/deploy.sh
# ==============================================

set -e

echo "=== Trading System Deploy ==="

# ── 1. Docker ─────────────────────────────────────────────
if ! command -v docker &> /dev/null; then
    echo "[1/6] Instaluję Docker..."
    apt-get update -q
    apt-get install -y ca-certificates curl gnupg
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -q
    apt-get install -y docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin
    echo "[1/6] Docker zainstalowany."
else
    echo "[1/6] Docker OK ($(docker --version))"
fi

# ── 2. Kod ────────────────────────────────────────────────
echo "[2/6] Aktualizuję kod..."
if [ -d ".git" ]; then
    git pull origin main
else
    echo "  Brak repo git — upewnij się, że pliki są na miejscu."
fi

# ── 3. .env ───────────────────────────────────────────────
echo "[3/6] Sprawdzam konfigurację..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "  Skopiowano .env.example -> .env"
        echo "  !! Uzupełnij .env przed uruchomieniem !!"
        echo "     nano .env"
        exit 1
    else
        echo "  BŁĄD: Brak .env i .env.example"
        exit 1
    fi
else
    echo "  .env OK"
fi

# ── 4. Build ──────────────────────────────────────────────
echo "[4/6] Buduję obrazy Docker..."
docker compose -f deploy/docker-compose.yml build --no-cache

# ── 5. Start ──────────────────────────────────────────────
echo "[5/6] Startuję kontenery..."
docker compose -f deploy/docker-compose.yml up -d

# ── 6. Status ─────────────────────────────────────────────
echo "[6/6] Sprawdzam status..."
sleep 5
docker compose -f deploy/docker-compose.yml ps

IP=$(hostname -I | awk '{print $1}')
PORT=$(grep DASHBOARD_PORT .env 2>/dev/null | cut -d= -f2 || echo 8000)

echo ""
echo "=== System uruchomiony ==="
echo "  Dashboard:  http://${IP}:${PORT:-8000}"
echo "  Logi core:  docker compose -f deploy/docker-compose.yml logs -f core"
echo "  Logi trader:docker compose -f deploy/docker-compose.yml logs -f trader"
echo ""
