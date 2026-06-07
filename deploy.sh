#!/usr/bin/env bash
# ─── Agent Black — One-Command VPS Deployer ────────────────────────────────────
# Run on any fresh VPS:
#   curl -sSL https://raw.githubusercontent.com/<you>/Agent-BlackV2/main/deploy.sh | bash
#
# Or clone + run locally:
#   git clone https://github.com/<you>/Agent-BlackV2.git && cd Agent-BlackV2
#   chmod +x deploy.sh && ./deploy.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
err()   { echo -e "${RED}[✗]${NC} $1" >&2; }

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || pwd)"
COMPOSE_FILE="$REPO_DIR/docker-compose.deploy.yml"

# ── 1. Check / install Docker ─────────────────────────────────────────────────
check_docker() {
    if ! command -v docker &>/dev/null; then
        warn "Docker not found. Installing..."
        curl -fsSL https://get.docker.com | sh
        sudo usermod -aG docker "$USER" 2>/dev/null || true
        info "Docker installed."
    else
        info "Docker found: $(docker --version)"
    fi

    if ! docker compose version &>/dev/null; then
        warn "Docker Compose plugin not found. Installing..."
        sudo apt-get update -qq && sudo apt-get install -y -qq docker-compose-plugin 2>/dev/null \
            || sudo yum install -y docker-compose-plugin 2>/dev/null \
            || { err "Could not install Docker Compose automatically."; exit 1; }
    fi
    info "Docker Compose: $(docker compose version)"
}

# ── 2. Check / create .env ────────────────────────────────────────────────────
setup_env() {
    if [[ ! -f "$REPO_DIR/.env" ]]; then
        if [[ -f "$REPO_DIR/.env.deploy" ]]; then
            cp "$REPO_DIR/.env.deploy" "$REPO_DIR/.env"
            warn "Created .env from .env.deploy — please edit it with your API keys:"
            echo ""
            echo "    nano $REPO_DIR/.env"
            echo ""
            read -rp "Press Enter once you've saved your .env file (or Ctrl+C to abort)..."
        else
            err "No .env.deploy template found. Create $REPO_DIR/.env manually."
            exit 1
        fi
    fi

    # Validate required vars
    source "$REPO_DIR/.env"
    if [[ -z "${GITHUB_OWNER:-}" || "${GITHUB_OWNER}" == "your-github-username" ]]; then
        err "GITHUB_OWNER is not set in .env — edit it before deploying."
        exit 1
    fi
    info "Environment loaded for owner: ${GITHUB_OWNER}"
}

# ── 3. Login to GHCR (only needed if images are private) ─────────────────────
ghcr_login() {
    if docker pull "ghcr.io/${GITHUB_OWNER}/agent-black/control-panel:latest" &>/dev/null; then
        info "GHCR images are accessible (public or already logged in)."
        return
    fi

    warn "Images appear private. Logging into GHCR..."
    if [[ -n "${GHCR_TOKEN:-}" ]]; then
        echo "$GHCR_TOKEN" | docker login ghcr.io -u "${GITHUB_OWNER}" --password-stdin
    else
        echo "To pull private GHCR images, you need a GitHub Personal Access Token."
        echo "Create one at: https://github.com/settings/tokens  (read:packages scope)"
        read -rp "Paste your GHCR token: " token
        echo "$token" | docker login ghcr.io -u "${GITHUB_OWNER}" --password-stdin
    fi
    info "Logged into GHCR."
}

# ── 4. Pull & start ───────────────────────────────────────────────────────────
deploy() {
    info "Pulling latest images..."
    docker compose -f "$COMPOSE_FILE" pull

    info "Starting services..."
    docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

    echo ""
    info "Deployment complete! Services are running:"
    echo ""
    echo "    Frontend   : http://$(hostname -I | awk '{print $1}'):8080"
    echo "    API (panel): http://localhost:8000"
    echo ""
    echo "    Useful commands:"
    echo "      docker compose -f $COMPOSE_FILE ps          # status"
    echo "      docker compose -f $COMPOSE_FILE logs -f     # logs"
    echo "      docker compose -f $COMPOSE_FILE restart     # restart"
    echo "      docker compose -f $COMPOSE_FILE down        # stop"
    echo ""
}

# ── 5. Health check ───────────────────────────────────────────────────────────
health_check() {
    info "Waiting for services to become healthy (max 90s)..."
    local max=90 elapsed=0
    while (( elapsed < max )); do
        if curl -sf http://localhost:8000/health &>/dev/null; then
            info "Control panel is healthy!"
            return
        fi
        sleep 5
        elapsed=$((elapsed + 5))
        printf "  ... %ds elapsed\r" "$elapsed"
    done
    warn "Health check timed out. Check logs: docker compose -f $COMPOSE_FILE logs"
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
    echo ""
    echo "  ╔══════════════════════════════════════════╗"
    echo "  ║   Agent Black — VPS Deployer             ║"
    echo "  ╚══════════════════════════════════════════╝"
    echo ""
    check_docker
    setup_env
    ghcr_login
    deploy
    health_check
}

main "$@"
