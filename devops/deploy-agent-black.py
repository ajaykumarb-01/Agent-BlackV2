import paramiko
import sys
import os
import tarfile
import io
import getpass
import time


# ─── CONFIGURE THESE ───────────────────────────────────────────────────────────
HOST = "64.227.177.219"
USER = "root"
PASSWORD = "Do12345@Do"

DOMAIN = "agentblack.hareeshworks.in"
EMAIL = "admin@agentblack.hareeshworks.in"

PROJECT_NAME = "agent-black"
APP_DIR = f"/opt/{PROJECT_NAME}"
CONTROL_PANEL_PORT = 8000
FRONTEND_PORT = 8080

# Local project root (parent of this devops/ folder)
LOCAL_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ──────────────────────────────────────────────────────────────────────────────


def run(client, command, timeout=120, print_output=True):
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    if print_output:
        log(command.split("\n")[0][:80], out, err, code)
    return code, out, err


def log(label, out, err, code):
    print(f"=== {label} ===")
    if out.strip():
        print(out.rstrip())
    if err.strip():
        print(err.rstrip())
    print(f"--- EXIT {code} ---")
    print()


def connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=HOST,
        username=USER,
        password=PASSWORD,
        timeout=20,
        allow_agent=False,
        look_for_keys=False,
    )
    return client


def upload_project(client):
    """Tar the project (excluding .git, node_modules, __pycache__, .idea, data, logs) and upload via SCP."""
    print(">>> Packaging project...")
    exclude_dirs = {".git", "node_modules", "__pycache__", ".idea", "data", "logs", ".tanstack", "dist"}
    exclude_files = {"*.pyc", "*.db", "*.sqlite"}

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for root, dirs, files in os.walk(LOCAL_PROJECT_ROOT):
            # Filter out excluded directories in-place
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.endswith(".pyc")]

            # Create paths relative to project root so tarball extracts directly into APP_DIR
            rel_root = os.path.relpath(root, LOCAL_PROJECT_ROOT)
            if rel_root == ".":
                rel_root = ""

            for f in files:
                if any(f.endswith(ext) for ext in [".pyc", ".db", ".sqlite"]):
                    continue
                local_path = os.path.join(root, f)
                arcname = os.path.join(rel_root, f).replace("\\", "/") if rel_root else f
                tar.add(local_path, arcname=arcname)

    buf.seek(0)
    tar_size = len(buf.getvalue())
    print(f"    Archive size: {tar_size / 1024 / 1024:.1f} MB")

    # Upload via SFTP
    print(">>> Uploading to server...")
    sftp = client.open_sftp()
    remote_tar = f"/tmp/{PROJECT_NAME}.tar.gz"
    sftp.putfo(buf, remote_tar)
    sftp.close()
    print(f"    Uploaded to {remote_tar}")

    # Extract on server
    print(">>> Extracting on server...")
    run(client, f"rm -rf {APP_DIR} /opt/Agent-BlackV2 && mkdir -p {APP_DIR}")
    run(client, f"tar -xzf {remote_tar} -C {APP_DIR}/")
    run(client, f"rm -f {remote_tar}")

    # Ensure the extracted dir matches APP_DIR
    # The tar creates /opt/agent-black/...
    run(client, f"ls -la {APP_DIR}/")
    print(">>> Project uploaded successfully.\n")


def generate_compose_file():
    """Generate docker-compose.yml for production deployment."""
    return f'''version: "3.9"

services:
  research-agent:
    build:
      context: .
      dockerfile: agents/research-agent/Dockerfile
    env_file: .env
    restart: unless-stopped
    networks:
      - agent-black-net

  solution-agent:
    build:
      context: .
      dockerfile: agents/solution-agent/Dockerfile
    env_file: .env
    restart: unless-stopped
    networks:
      - agent-black-net

  experiment-agent:
    build:
      context: .
      dockerfile: agents/experiment-agent/Dockerfile
    env_file: .env
    restart: unless-stopped
    networks:
      - agent-black-net

  control-panel:
    build:
      context: .
      dockerfile: agents/host-agent/Dockerfile.control-panel
    ports:
      - "127.0.0.1:{CONTROL_PANEL_PORT}:{CONTROL_PANEL_PORT}"
    env_file: .env
    depends_on:
      - research-agent
      - solution-agent
      - experiment-agent
    restart: unless-stopped
    networks:
      - agent-black-net

  frontend:
    build:
      context: .
      dockerfile: devops/Dockerfile.frontend
    ports:
      - "127.0.0.1:{FRONTEND_PORT}:{FRONTEND_PORT}"
    env_file: .env
    depends_on:
      - control-panel
    restart: unless-stopped
    networks:
      - agent-black-net

networks:
  agent-black-net:
    driver: bridge
'''


def generate_frontend_dockerfile():
    """Generate Dockerfile for the TanStack Start frontend."""
    return '''FROM node:20-slim AS builder
WORKDIR /app
COPY ui/package.json ui/bun.lock* ui/package-lock.json* ./
RUN npm install --legacy-peer-deps
COPY ui/ ./
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=builder /app ./
EXPOSE 8080
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "8080"]
'''


def generate_env_file():
    """Generate .env for production."""
    return f'''# ── Agent Black Production Config ─────────────────────
HOST=0.0.0.0
PORT={CONTROL_PANEL_PORT}
DOCKER_BUILDKIT=1
COMPOSE_PROJECT_NAME={PROJECT_NAME}
VITE_API_URL=https://{DOMAIN}/api

# ── Agent Ports (internal Docker networking) ──────────
RESEARCH_AGENT_HOST=research-agent
RESEARCH_AGENT_PORT=8001
SOLUTION_AGENT_HOST=solution-agent
SOLUTION_AGENT_PORT=8002
EXPERIMENT_AGENT_HOST=experiment-agent
EXPERIMENT_AGENT_PORT=8003

# ── Domain ────────────────────────────────────────────
DOMAIN={DOMAIN}
BASE_URL=https://{DOMAIN}
FRONTEND_PORT={FRONTEND_PORT}
'''


def generate_nginx_config():
    """Generate Nginx config for Agent Black."""
    return f'''server {{
    listen 80;
    listen [::]:80;
    server_name {DOMAIN};

    # Frontend (TanStack Start)
    location / {{
        proxy_pass http://127.0.0.1:{FRONTEND_PORT};
        proxy_set_header Host \\$host;
        proxy_set_header X-Real-IP \\$remote_addr;
        proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }}

    # Control Panel API
    location /api/ {{
        proxy_pass http://127.0.0.1:{CONTROL_PANEL_PORT}/api/;
        proxy_set_header Host \\$host;
        proxy_set_header X-Real-IP \\$remote_addr;
        proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\$scheme;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }}

    # SSE streaming endpoints
    location /api/query/stream/ {{
        proxy_pass http://127.0.0.1:{CONTROL_PANEL_PORT}/api/query/stream/;
        proxy_set_header Host \\$host;
        proxy_set_header X-Real-IP \\$remote_addr;
        proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\$scheme;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
        chunked_transfer_encoding on;
    }}
}}
'''


def setup(client):
    """Full fresh install: Docker, Nginx, SSL, build & deploy Agent Black."""
    # Step 1: Upload project files
    upload_project(client)

    # Step 2: Write docker-compose.yml
    print(">>> Writing docker-compose.yml...")
    sftp = client.open_sftp()
    with sftp.open(f"{APP_DIR}/docker-compose.yml", "w") as f:
        f.write(generate_compose_file())
    sftp.close()

    # Step 2b: Write frontend Dockerfile
    print(">>> Writing frontend Dockerfile...")
    run(client, f"mkdir -p {APP_DIR}/devops")
    sftp = client.open_sftp()
    with sftp.open(f"{APP_DIR}/devops/Dockerfile.frontend", "w") as f:
        f.write(generate_frontend_dockerfile())
    sftp.close()

    # Step 2c: Write .env
    print(">>> Writing .env file...")
    sftp = client.open_sftp()
    with sftp.open(f"{APP_DIR}/.env", "w") as f:
        f.write(generate_env_file())
    sftp.close()

    # Step 3: Install system packages, Docker, Nginx, Certbot
    print(">>> Installing system packages and Docker...")
    bootstrap = f'''
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

# ── System packages ──
apt update
apt install -y ca-certificates curl gnupg lsb-release openssl git ufw

# ── Docker repo ──
install -m 0755 -d /etc/apt/keyrings
if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
fi
cat >/etc/apt/sources.list.d/docker.list <<EOF
deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable
EOF
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl enable --now docker

# ── Nginx ──
apt install -y nginx
systemctl enable --now nginx

# ── Certbot ──
apt install -y certbot python3-certbot-nginx

echo ">>> System packages installed."
'''
    code, out, err = run(client, bootstrap, timeout=600)
    log("SYSTEM PACKAGES", out, err, code)

    # Step 4: Build and start with Docker Compose
    print(">>> Building and starting Docker containers...")
    build_cmd = f'''
set -euo pipefail
cd {APP_DIR}
docker compose down --remove-orphans || true
docker compose build --no-cache
docker compose up -d
echo ">>> Waiting for services to start..."
sleep 10
docker compose ps
'''
    code, out, err = run(client, build_cmd, timeout=1800)
    log("DOCKER BUILD & START", out, err, code)

    # Step 5: Configure Nginx
    print(">>> Configuring Nginx...")
    nginx_config = generate_nginx_config()
    sftp = client.open_sftp()
    with sftp.open("/etc/nginx/sites-available/agentblack", "w") as f:
        f.write(nginx_config)
    sftp.close()

    code, out, err = run(client, '''
set -euo pipefail
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/agentblack /etc/nginx/sites-enabled/agentblack
nginx -t
systemctl enable --now nginx
systemctl reload nginx
''', timeout=60)
    log("NGINX CONFIG", out, err, code)

    # Step 6: Firewall
    print(">>> Configuring firewall...")
    code, out, err = run(client, '''
ufw allow 22/tcp || true
ufw allow 80/tcp || true
ufw allow 443/tcp || true
ufw --force enable
''', timeout=60)
    log("FIREWALL", out, err, code)

    # Step 7: SSL certificate
    print(">>> Obtaining SSL certificate...")
    code, out, err = run(client, f'''
certbot --nginx -d {DOMAIN} --email {EMAIL} --agree-tos --non-interactive || true
systemctl reload nginx
''', timeout=300)
    log("SSL CERTIFICATE", out, err, code)

    # Step 8: Health check
    print(">>> Running health checks...")
    code, out, err = run(client, f'''
echo "=== Docker Status ==="
cd {APP_DIR} && docker compose ps

echo ""
echo "=== Control Panel Health ==="
curl -fsS http://127.0.0.1:{CONTROL_PANEL_PORT}/api/status || echo "Control panel not responding"

echo ""
echo "=== Nginx Test ==="
nginx -t 2>&1

echo ""
echo "=== SSL Certs ==="
certbot certificates 2>/dev/null || true

echo ""
echo "=== Site Accessible ==="
curl -fsS -o /dev/null -w "HTTP Status: %{{http_code}}" https://{DOMAIN}/ || echo "Site not accessible yet"
''', timeout=120)
    log("HEALTH CHECK", out, err, code)

    print("\n" + "=" * 60)
    print(f"  DEPLOYMENT COMPLETE!")
    print(f"  Site URL  : https://{DOMAIN}")
    print(f"  API URL   : https://{DOMAIN}/api/")
    print(f"  Server    : {USER}@{HOST}")
    print("=" * 60)


def check_status(client):
    """Check server status."""
    commands = [
        ("System Packages", "dpkg -l docker-ce docker-ce-cli containerd.io nginx certbot ufw 2>/dev/null | tail -n +6 || true"),
        ("Services", "systemctl is-active docker nginx ufw 2>/dev/null || true"),
        ("Docker Containers", f"cd {APP_DIR} && docker compose ps 2>/dev/null || docker ps --format '{{{{.Names}}}} {{{{.Status}}}} {{{{.Ports}}}}' 2>/dev/null || true"),
        ("Env File", f"test -f {APP_DIR}/.env && echo env_exists || echo no_env"),
        ("Nginx Site", "test -f /etc/nginx/sites-enabled/agentblack && echo nginx_site || echo no_site"),
        ("Nginx Test", "nginx -t 2>&1 || true"),
        ("SSL Certs", "certbot certificates 2>/dev/null || true"),
        ("Control Panel", f"curl -fsS http://127.0.0.1:{CONTROL_PANEL_PORT}/api/status 2>/dev/null || echo 'not responding'"),
        ("Container Logs", f"cd {APP_DIR} && docker compose logs --tail 10 2>/dev/null || true"),
    ]
    for label, cmd in commands:
        code, out, err = run(client, cmd, timeout=180)
        log(label, out, err, code)


def update_version(client):
    """Pull latest code, rebuild containers, and restart."""
    print(">>> Uploading updated project...")
    upload_project(client)

    # Rewrite docker-compose and env
    sftp = client.open_sftp()
    with sftp.open(f"{APP_DIR}/docker-compose.yml", "w") as f:
        f.write(generate_compose_file())
    sftp.close()

    sftp = client.open_sftp()
    with sftp.open(f"{APP_DIR}/.env", "w") as f:
        f.write(generate_env_file())
    sftp.close()

    run(client, f"mkdir -p {APP_DIR}/devops")
    sftp = client.open_sftp()
    with sftp.open(f"{APP_DIR}/devops/Dockerfile.frontend", "w") as f:
        f.write(generate_frontend_dockerfile())
    sftp.close()

    code, out, err = run(client, f'''
set -euo pipefail
cd {APP_DIR}

echo ">>> Stopping containers..."
docker compose down --remove-orphans || true

echo ">>> Rebuilding images..."
docker compose build --no-cache

echo ">>> Starting containers..."
docker compose up -d

echo ">>> Waiting for services..."
sleep 10

echo ">>> Container status:"
docker compose ps

echo ">>> Health check:"
curl -fsS http://127.0.0.1:{CONTROL_PANEL_PORT}/api/status || echo "Control panel not responding"

echo ">>> Cleaning old images:"
docker image prune -f || true
''', timeout=1800)
    log("UPDATE COMPLETE", out, err, code)


def restart_services(client):
    """Restart all Docker containers and Nginx."""
    code, out, err = run(client, f'''
set -euo pipefail
cd {APP_DIR}

echo ">>> Restarting Docker containers..."
docker compose restart

echo ">>> Restarting Nginx..."
systemctl restart nginx

echo ">>> Service status:"
docker compose ps
systemctl is-active docker nginx

echo ">>> Health check:"
curl -fsS http://127.0.0.1:{CONTROL_PANEL_PORT}/api/status || echo "Control panel not responding"
''', timeout=300)
    log("RESTART COMPLETE", out, err, code)


def view_logs(client):
    """View recent logs from all containers."""
    code, out, err = run(client, f'''
cd {APP_DIR}
echo "=== Control Panel Logs ==="
docker compose logs --tail 30 control-panel 2>/dev/null || echo "No control panel logs"

echo ""
echo "=== Research Agent Logs ==="
docker compose logs --tail 15 research-agent 2>/dev/null || echo "No research agent logs"

echo ""
echo "=== Solution Agent Logs ==="
docker compose logs --tail 15 solution-agent 2>/dev/null || echo "No solution agent logs"

echo ""
echo "=== Experiment Agent Logs ==="
docker compose logs --tail 15 experiment-agent 2>/dev/null || echo "No experiment agent logs"

echo ""
echo "=== Frontend Logs ==="
docker compose logs --tail 15 frontend 2>/dev/null || echo "No frontend logs"

echo ""
echo "=== Nginx Error Log ==="
tail -20 /var/log/nginx/error.log 2>/dev/null || true
''', timeout=120)
    log("LOGS", out, err, code)


def renew_ssl(client):
    """Renew SSL certificate."""
    code, out, err = run(client, f'''
set -euo pipefail
echo ">>> Current certificates:"
certbot certificates 2>/dev/null || true

echo ">>> Attempting certificate renewal..."
certbot renew --non-interactive || true

echo ">>> Reloading nginx..."
nginx -t && systemctl reload nginx

echo ">>> Certificates after renewal:"
certbot certificates 2>/dev/null || true
''', timeout=300)
    log("SSL RENEW COMPLETE", out, err, code)


def full_update(client):
    """System packages + Docker image rebuild + SSL renewal."""
    print(">>> Uploading latest code...")
    upload_project(client)

    sftp = client.open_sftp()
    with sftp.open(f"{APP_DIR}/docker-compose.yml", "w") as f:
        f.write(generate_compose_file())
    sftp.close()

    sftp = client.open_sftp()
    with sftp.open(f"{APP_DIR}/.env", "w") as f:
        f.write(generate_env_file())
    sftp.close()

    run(client, f"mkdir -p {APP_DIR}/devops")
    sftp = client.open_sftp()
    with sftp.open(f"{APP_DIR}/devops/Dockerfile.frontend", "w") as f:
        f.write(generate_frontend_dockerfile())
    sftp.close()

    code, out, err = run(client, f'''
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

echo ">>> Updating system packages..."
apt update && apt upgrade -y || true

echo ">>> Updating Docker..."
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin || true

echo ">>> Updating Nginx and Certbot..."
apt install -y nginx certbot python3-certbot-nginx || true

cd {APP_DIR}

echo ">>> Rebuilding Docker containers..."
docker compose down --remove-orphans || true
docker compose build --no-cache
docker compose up -d

echo ">>> Waiting for services..."
sleep 10

echo ">>> Attempting SSL renewal..."
certbot renew --non-interactive || true
nginx -t && systemctl reload nginx

echo ">>> Cleaning old Docker images..."
docker image prune -f || true

echo ">>> Final status:"
docker compose ps
curl -fsS http://127.0.0.1:{CONTROL_PANEL_PORT}/api/status || echo "Control panel not responding"
certbot certificates 2>/dev/null || true
''', timeout=3600)
    log("FULL UPDATE COMPLETE", out, err, code)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 60)
    print("  AGENT BLACK - REMOTE SERVER DEPLOYMENT MANAGER")
    print("=" * 60)
    print(f"  Server : {USER}@{HOST}")
    print(f"  Domain : {DOMAIN}")
    print(f"  Email  : {EMAIL}")
    print(f"  Project: {PROJECT_NAME}")
    print("=" * 60)
    print()
    print("  1) setup        - Full deploy (Docker, Nginx, SSL, build all services)")
    print("  2) status       - Check server & container status")
    print("  3) update       - Upload code & rebuild containers")
    print("  4) restart      - Restart all services")
    print("  5) logs         - View recent container logs")
    print("  6) ssl-renew    - Renew SSL certificate & reload Nginx")
    print("  7) full-update  - System packages + rebuild + SSL renewal")
    print()

    choice = input("  Enter choice (1-7): ").strip()

    actions = {
        "1": ("setup", setup),
        "2": ("status", check_status),
        "3": ("update", update_version),
        "4": ("restart", restart_services),
        "5": ("logs", view_logs),
        "6": ("ssl-renew", renew_ssl),
        "7": ("full-update", full_update),
    }

    if choice not in actions:
        print("  Invalid choice.")
        return

    action_name, action_fn = actions[choice]
    print(f"\n  Running: {action_name} ...\n")

    client = connect()
    action_fn(client)
    client.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
