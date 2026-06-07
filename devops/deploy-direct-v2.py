
EMAIL = "admin@agentblack.hareeshworks.in"
import paramiko
import sys
import os
import tarfile
import io
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ─── CONFIGURE THESE ───────────────────────────────────────────────────────────
HOST = "64.227.177.219"
USER = "root"
PASSWORD = "Do12345@Do"

DOMAIN = "agentblack.hareeshworks.in"
PROJECT_NAME = "agent-black"
APP_DIR = f"/opt/{PROJECT_NAME}"
CONTROL_PANEL_PORT = 8000
FRONTEND_PORT = 3000

LOCAL_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ──────────────────────────────────────────────────────────────────────────────


def connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=HOST, username=USER, password=PASSWORD, timeout=60,
                   allow_agent=False, look_for_keys=False)
    return client


def run(client, cmd, timeout=300):
    transport = client.get_transport()
    ch = transport.open_session()
    ch.settimeout(timeout)
    ch.exec_command(cmd)
    out_lines, err_lines = [], []
    while not ch.exit_status_ready():
        time.sleep(0.5)
    while ch.recv_ready():
        out_lines.append(ch.recv(65536).decode("utf-8", errors="replace"))
    while ch.recv_stderr_ready():
        err_lines.append(ch.recv_stderr(65536).decode("utf-8", errors="replace"))
    code = ch.recv_exit_status()
    ch.close()
    out = "".join(out_lines)
    err = "".join(err_lines)
    label = cmd.split("\n")[0][:80]
    print(f"--- {label} (exit {code}) ---")
    if out.strip(): print(out.rstrip())
    if err.strip(): print(err.rstrip())
    print()
    return code, out, err


def sftp_write(client, remote_path, content):
    sftp = client.open_sftp()
    with sftp.open(remote_path, "w") as f:
        f.write(content)
    sftp.close()


# ─── Upload Project (Preserve data/ and logs/) ────────────────────────────────
def upload_project(client):
    print(">>> Packaging project...")
    exclude_dirs = {".git", "node_modules", "__pycache__", ".idea", "data", "logs",
                    ".tanstack", "plans", "dist", ".output"}
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for root, dirs, files in os.walk(LOCAL_PROJECT_ROOT):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            rel = os.path.relpath(root, LOCAL_PROJECT_ROOT)
            if rel == ".":
                rel = ""
            for f in files:
                if any(f.endswith(e) for e in [".pyc", ".db", ".sqlite"]):
                    continue
                local = os.path.join(root, f)
                arc = os.path.join(rel, f).replace("\\", "/") if rel else f
                tar.add(local, arcname=arc)
    buf.seek(0)
    print(f"    Archive: {len(buf.getvalue()) / 1024 / 1024:.1f} MB")
    sftp = client.open_sftp()
    sftp.putfo(buf, f"/tmp/{PROJECT_NAME}.tar.gz")
    sftp.close()

    # ── Backup data/ and logs/ before wiping ──
    run(client, f"""
set -euo pipefail
backup_dir="$(mktemp -d)"
if [ -d {APP_DIR}/data ]; then cp -a {APP_DIR}/data "$backup_dir/data"; fi
if [ -d {APP_DIR}/logs ]; then cp -a {APP_DIR}/logs "$backup_dir/logs"; fi
rm -rf {APP_DIR}
mkdir -p {APP_DIR}
if [ -d "$backup_dir/data" ]; then cp -a "$backup_dir/data" {APP_DIR}/data; fi
if [ -d "$backup_dir/logs" ]; then cp -a "$backup_dir/logs" {APP_DIR}/logs; fi
rm -rf "$backup_dir"
echo ">>> data/ and logs/ preserved"
""")

    run(client, f"tar -xzf /tmp/{PROJECT_NAME}.tar.gz -C {APP_DIR}/")
    run(client, "rm -f /tmp/agent-black.tar.gz")
    print(">>> Project uploaded.\n")


# ─── Swap Space ───────────────────────────────────────────────────────────────
def setup_swap(client):
    print(">>> Setting up swap space...")
    run(client, """
set -euo pipefail
if [ ! -f /swapfile ]; then
  fallocate -l 1G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
  echo ">>> 1GB swap created"
else
  echo ">>> Swap already exists"
fi
free -h
""", timeout=60)


# ─── Node.js 22 ───────────────────────────────────────────────────────────────
def install_nodejs(client):
    run(client, """
set -euo pipefail
current_node=$(node -v 2>/dev/null || echo "none")
if [[ "$current_node" != v22* ]]; then
  echo ">>> Installing Node.js 22 (was $current_node)..."
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
  apt install -y nodejs
else
  echo ">>> Node.js $current_node OK"
fi
""", timeout=120)


# ─── Frontend Build ───────────────────────────────────────────────────────────
def build_frontend(client):
    print(">>> Building frontend on VPS...")
    run(client, f"""
set -euo pipefail
cd {APP_DIR}/ui
export NODE_OPTIONS="--max-old-space-size=768"
npm install --legacy-peer-deps
npm run build

echo ""
echo ">>> Build output (dist/):"
find dist -maxdepth 3 -type f 2>/dev/null | sort | head -40 || echo "(no dist/)"
echo ""
echo ">>> Build output (.output/):"
find .output -maxdepth 3 -type f 2>/dev/null | sort | head -40 || echo "(no .output/)"
""", timeout=600)


# ─── Python Setup ─────────────────────────────────────────────────────────────
def setup_python(client):
    print(">>> Setting up Python environment...")
    run(client, f"""
set -euo pipefail
cd {APP_DIR}
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install uvicorn[standard]
""", timeout=300)


# ─── Server Wrapper (Dynamic SSR Entry) ───────────────────────────────────────
def write_frontend_wrapper(client):
    sftp_write(client, f"{APP_DIR}/ui/server-wrapper.mjs", r"""
import { createServer } from 'node:http';
import { access, readFile } from 'node:fs/promises';
import { join, extname } from 'node:path';
import { pathToFileURL } from 'node:url';

const PORT = process.env.PORT || 3000;
const ROOT = import.meta.dirname;

const PUBLIC_DIRS = [
  join(ROOT, 'dist', 'client'),
  join(ROOT, '.output', 'public'),
  join(ROOT, 'dist', 'public'),
];

const SERVER_ENTRIES = [
  join(ROOT, '.output', 'server', 'index.mjs'),
  join(ROOT, 'dist', 'server', 'index.mjs'),
  join(ROOT, 'dist', 'server', 'index.js'),
  join(ROOT, 'dist', 'server', 'server.js'),
];

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript',
  '.mjs': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
};

async function firstExisting(paths) {
  for (const p of paths) {
    try { await access(p); return p; } catch {}
  }
  return undefined;
}

const PUBLIC_DIR = await firstExisting(PUBLIC_DIRS);

if (!PUBLIC_DIR) {
  console.error('No public directory found. Checked:', PUBLIC_DIRS);
} else {
  console.log('Using public dir:', PUBLIC_DIR);
}

let ssrHandler;
async function getSSRHandler() {
  if (!ssrHandler) {
    const entryPath = await firstExisting(SERVER_ENTRIES);
    if (!entryPath) {
      const tried = SERVER_ENTRIES.map(p => p.replace(ROOT, '.')).join(', ');
      throw new Error(`SSR entry not found. Tried: ${tried}`);
    }
    console.log('Loading SSR entry:', entryPath);
    const mod = await import(pathToFileURL(entryPath).href);
    const entry = mod.default || mod;
    if (entry.fetch) {
      ssrHandler = entry;
    } else if (typeof entry === 'function') {
      ssrHandler = { fetch: entry };
    } else {
      throw new Error('SSR entry has no fetch handler: ' + entryPath);
    }
  }
  return ssrHandler;
}

const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://localhost:${PORT}`);

    // Serve static files first
    if (PUBLIC_DIR) {
      const isNotHtmlRequest = url.pathname !== '/' || !req.headers.accept?.includes('text/html');
      if (isNotHtmlRequest) {
        try {
          const filePath = join(PUBLIC_DIR, url.pathname);
          const content = await readFile(filePath);
          const ext = extname(filePath);
          res.writeHead(200, {
            'Content-Type': MIME[ext] || 'application/octet-stream',
            'Cache-Control': ext !== '.html' ? 'public, max-age=31536000, immutable' : 'no-cache',
          });
          res.end(content);
          return;
        } catch {}
      }
    }

    // SSR fallback
    const handler = await getSSRHandler();
    const headers = new Headers();
    for (const [key, value] of Object.entries(req.headers)) {
      if (value) headers.set(key, Array.isArray(value) ? value.join(', ') : value);
    }

    let body = undefined;
    if (['POST', 'PUT', 'PATCH'].includes(req.method)) {
      const chunks = [];
      for await (const chunk of req) chunks.push(chunk);
      body = Buffer.concat(chunks);
    }

    const response = await handler.fetch(new Request(url.href, {
      method: req.method,
      headers,
      body,
    }));

    const resHeaders = {};
    response.headers.forEach((v, k) => { resHeaders[k] = v; });
    res.writeHead(response.status, resHeaders);

    if (response.body) {
      const reader = response.body.getReader();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        res.write(value);
      }
    }
    res.end();
  } catch (error) {
    console.error('SSR error:', error.stack || error.message);
    res.writeHead(500, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end('<!DOCTYPE html><html><body><h1>500</h1><pre>SSR error</pre></body></html>');
  }
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`Agent Black Frontend running on http://0.0.0.0:${PORT}`);
});
""")


# ─── Environment File ─────────────────────────────────────────────────────────
def write_env(client):
    sftp_write(client, f"{APP_DIR}/.env", f"""HOST=0.0.0.0
PORT={CONTROL_PANEL_PORT}
DOMAIN={DOMAIN}
BASE_URL=https://{DOMAIN}
VITE_API_URL=https://{DOMAIN}/api
RESEARCH_AGENT_HOST=127.0.0.1
RESEARCH_AGENT_PORT=8001
SOLUTION_AGENT_HOST=127.0.0.1
SOLUTION_AGENT_PORT=8002
EXPERIMENT_AGENT_HOST=127.0.0.1
EXPERIMENT_AGENT_PORT=8003
""")


# ─── Nginx Config ─────────────────────────────────────────────────────────────
def write_nginx_config(client, ssl=False):
    if ssl:
        sftp_write(client, "/etc/nginx/sites-available/agentblack", f"""server {{
    listen 80;
    listen [::]:80;
    server_name {DOMAIN};
    return 301 https://$host$request_uri;
}}

server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name {DOMAIN};

    ssl_certificate /etc/letsencrypt/live/{DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{DOMAIN}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {{
        proxy_pass http://127.0.0.1:{FRONTEND_PORT};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }}

    location /api/query/stream/ {{
        proxy_pass http://127.0.0.1:{CONTROL_PANEL_PORT}/api/query/stream/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
        chunked_transfer_encoding on;
    }}

    location /api/ {{
        proxy_pass http://127.0.0.1:{CONTROL_PANEL_PORT}/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }}

    location /assets/ {{
        proxy_pass http://127.0.0.1:{FRONTEND_PORT}/assets/;
        proxy_set_header Host $host;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }}
}}
""")
    else:
        sftp_write(client, "/etc/nginx/sites-available/agentblack", f"""server {{
    listen 80;
    listen [::]:80;
    server_name {DOMAIN};

    location / {{
        proxy_pass http://127.0.0.1:{FRONTEND_PORT};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }}

    location /api/query/stream/ {{
        proxy_pass http://127.0.0.1:{CONTROL_PANEL_PORT}/api/query/stream/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
        chunked_transfer_encoding on;
    }}

    location /api/ {{
        proxy_pass http://127.0.0.1:{CONTROL_PANEL_PORT}/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }}

    location /assets/ {{
        proxy_pass http://127.0.0.1:{FRONTEND_PORT}/assets/;
        proxy_set_header Host $host;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }}
}}
""")


# ─── Systemd Services ─────────────────────────────────────────────────────────
def write_systemd_services(client):
    sftp_write(client, "/etc/systemd/system/agent-black-frontend.service", f"""[Unit]
Description=Agent Black Frontend (TanStack Start)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={APP_DIR}/ui
Environment=NODE_ENV=production
Environment=PORT={FRONTEND_PORT}
Environment=NODE_OPTIONS=--max-old-space-size=384
ExecStart=/usr/bin/node server-wrapper.mjs
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
""")
    sftp_write(client, "/etc/systemd/system/agent-black-panel.service", f"""[Unit]
Description=Agent Black Control Panel
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={APP_DIR}
Environment=PATH={APP_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart={APP_DIR}/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port {CONTROL_PANEL_PORT} --log-level info
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
""")
    sftp_write(client, "/etc/systemd/system/agent-black-research.service", f"""[Unit]
Description=Agent Black Research Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={APP_DIR}/agents/research-agent
Environment=PATH={APP_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart={APP_DIR}/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8001 --log-level info
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
""")
    sftp_write(client, "/etc/systemd/system/agent-black-solution.service", f"""[Unit]
Description=Agent Black Solution Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={APP_DIR}/agents/solution-agent
Environment=PATH={APP_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart={APP_DIR}/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8002 --log-level info
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
""")
    sftp_write(client, "/etc/systemd/system/agent-black-experiment.service", f"""[Unit]
Description=Agent Black Experiment Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={APP_DIR}/agents/experiment-agent
Environment=PATH={APP_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart={APP_DIR}/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8003 --log-level info
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
""")


# ─── Full Setup (Option 1) ───────────────────────────────────────────────────
def setup(client):
    upload_project(client)
    setup_swap(client)

    print(">>> Installing system packages...")
    run(client, """
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt update
apt install -y ca-certificates curl gnupg lsb-release openssl git ufw \
    python3 python3-venv python3-pip \
    nginx certbot python3-certbot-nginx
""", timeout=300)

    install_nodejs(client)
    build_frontend(client)
    setup_python(client)

    write_frontend_wrapper(client)
    write_env(client)

    write_systemd_services(client)
    write_nginx_config(client, ssl=False)

    print(">>> Configuring firewall...")
    run(client, "ufw allow 22/tcp || true; ufw allow 80/tcp || true; ufw allow 443/tcp || true; ufw --force enable", timeout=30)

    print(">>> Starting services...")
    run(client, """
set -euo pipefail
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/agentblack /etc/nginx/sites-enabled/agentblack
nginx -t
systemctl enable --now nginx
systemctl reload nginx
systemctl daemon-reload
systemctl enable --now agent-black-frontend
systemctl enable --now agent-black-research
systemctl enable --now agent-black-solution
systemctl enable --now agent-black-experiment
systemctl enable --now agent-black-panel
sleep 5
""", timeout=60)

    print(">>> Obtaining SSL certificate...")
    run(client, f"certbot --nginx -d {DOMAIN} --email {EMAIL} --agree-tos --non-interactive 2>&1 || true", timeout=300)

    write_nginx_config(client, ssl=True)
    run(client, "nginx -t && systemctl reload nginx")

    time.sleep(2)
    print(">>> Final verification...")
    run(client, f"""
echo "=== Services ==="
systemctl is-active agent-black-frontend agent-black-panel agent-black-research agent-black-solution agent-black-experiment nginx

echo ""
echo "=== Health ==="
curl -s -o /dev/null -w "HTTPS: %{{http_code}}" https://{DOMAIN}/
echo ""
curl -s -o /dev/null -w "Frontend: %{{http_code}}" http://127.0.0.1:{FRONTEND_PORT}/
echo ""
curl -s http://127.0.0.1:{CONTROL_PANEL_PORT}/ | head -1
echo ""
free -h
""", timeout=30)

    print("\n" + "=" * 60)
    print("  DEPLOYMENT COMPLETE!")
    print(f"  Site : https://{DOMAIN}")
    print(f"  API  : https://{DOMAIN}/api/")
    print("=" * 60)


# ─── Update Version (Option 3) ────────────────────────────────────────────────
def update_version(client):
    upload_project(client)
    setup_swap(client)
    install_nodejs(client)
    build_frontend(client)
    setup_python(client)

    write_frontend_wrapper(client)
    write_env(client)

    # Check if SSL cert exists
    _, cert_check, _ = run(client, f"certbot certificates 2>/dev/null | grep -c '{DOMAIN}' || echo 0", timeout=10)
    has_ssl = "1" in cert_check

    write_nginx_config(client, ssl=has_ssl)
    write_systemd_services(client)

    print(">>> Restarting services...")
    run(client, """
set -euo pipefail
systemctl daemon-reload
nginx -t && systemctl reload nginx
systemctl restart agent-black-frontend
systemctl restart agent-black-research
systemctl restart agent-black-solution
systemctl restart agent-black-experiment
systemctl restart agent-black-panel
sleep 5
""", timeout=120)

    time.sleep(2)
    run(client, f"""
echo "=== Services ==="
systemctl is-active agent-black-frontend agent-black-panel agent-black-research agent-black-solution agent-black-experiment nginx
echo ""
curl -s -o /dev/null -w "HTTPS: %{{http_code}}" https://{DOMAIN}/ || echo "HTTPS failed"
echo ""
curl -s -o /dev/null -w "Frontend: %{{http_code}}" http://127.0.0.1:{FRONTEND_PORT}/
echo ""
free -h
""", timeout=30)


# ─── Restart Services (Option 4) ─────────────────────────────────────────────
def restart_services(client):
    run(client, """
set -euo pipefail
systemctl daemon-reload
systemctl restart agent-black-frontend agent-black-research agent-black-solution agent-black-experiment agent-black-panel
systemctl reload nginx
sleep 3
systemctl is-active agent-black-frontend agent-black-panel agent-black-research agent-black-solution agent-black-experiment nginx
""", timeout=60)


# ─── View Logs (Option 5) ────────────────────────────────────────────────────
def view_logs(client):
    run(client, """
echo "=== Frontend ==="
journalctl -u agent-black-frontend --no-pager -n 20
echo ""
echo "=== Control Panel ==="
journalctl -u agent-black-panel --no-pager -n 20
echo ""
echo "=== Nginx ==="
tail -10 /var/log/nginx/error.log 2>/dev/null || true
""", timeout=30)


# ─── Check Status (Option 2) ─────────────────────────────────────────────────
def check_status(client):
    run(client, f"""
echo "=== Services ==="
systemctl is-active agent-black-frontend agent-black-panel agent-black-research agent-black-solution agent-black-experiment nginx 2>/dev/null
echo ""
echo "=== Health ==="
curl -s -o /dev/null -w "HTTPS: %{{http_code}}\\n" https://{DOMAIN}/ 2>/dev/null || echo "HTTPS: failed"
curl -s -o /dev/null -w "Frontend: %{{http_code}}\\n" http://127.0.0.1:{FRONTEND_PORT}/ || echo "Frontend: failed"
curl -s http://127.0.0.1:{CONTROL_PANEL_PORT}/ | head -1 || echo "Panel: failed"
echo ""
free -h
""", timeout=30)


# ─── Resetup - Wipe Everything & Redeploy (Option 7) ─────────────────────────
def resetup(client):
    print(">>> WARNING: This will DESTROY all data, logs, database, SSL cert,")
    print("    and reinstall everything from scratch.")
    confirm = input("    Type 'YES WIPE' to confirm: ").strip()
    if confirm != "YES WIPE":
        print("    Aborted.")
        return

    print("\n>>> Stopping all services...")
    run(client, """
set -euo pipefail
systemctl stop agent-black-frontend agent-black-panel agent-black-research \
    agent-black-solution agent-black-experiment 2>/dev/null || true
systemctl disable agent-black-frontend agent-black-panel agent-black-research \
    agent-black-solution agent-black-experiment 2>/dev/null || true
""", timeout=30)

    print(">>> Removing old systemd services...")
    run(client, """
rm -f /etc/systemd/system/agent-black-frontend.service
rm -f /etc/systemd/system/agent-black-panel.service
rm -f /etc/systemd/system/agent-black-research.service
rm -f /etc/systemd/system/agent-black-solution.service
rm -f /etc/systemd/system/agent-black-experiment.service
systemctl daemon-reload
""", timeout=30)

    print(">>> Removing old app directory (data, logs, DB, venv, dist)...")
    run(client, f"rm -rf {APP_DIR}", timeout=30)

    print(">>> Removing SSL certificate...")
    run(client, f"certbot delete --non-interactive --cert-name {DOMAIN} 2>/dev/null || true", timeout=60)

    print(">>> Removing nginx config...")
    run(client, """
rm -f /etc/nginx/sites-available/agentblack
rm -f /etc/nginx/sites-enabled/agentblack
ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default 2>/dev/null || true
systemctl reload nginx 2>/dev/null || true
""", timeout=30)

    print("\n>>> Starting fresh setup...\n")
    setup(client)


# ─── Renew SSL (Option 6) ────────────────────────────────────────────────────
def renew_ssl(client):
    run(client, "certbot renew --non-interactive || true; nginx -t && systemctl reload nginx", timeout=300)


# ─── Fix SSR Error (Option 8) ────────────────────────────────────────────────
def fix_ssr(client):
    """Rebuild frontend + rewrite server-wrapper.mjs without touching anything else."""
    print(">>> Checking current build output...")
    run(client, f"""
cd {APP_DIR}/ui
echo "--- Current dist/ structure ---"
find dist/ -type f -name "*.js" -o -name "*.mjs" 2>/dev/null | head -20
echo "--- Current .output/ structure ---"
find .output/ -type f -name "*.js" -o -name "*.mjs" 2>/dev/null | head -20
echo ""
echo "--- server-wrapper.mjs exists? ---"
ls -la server-wrapper.mjs 2>/dev/null || echo "server-wrapper.mjs NOT FOUND"
""", timeout=15)

    print(">>> Rebuilding frontend...")
    run(client, f"""
set -euo pipefail
cd {APP_DIR}/ui
export NODE_OPTIONS="--max-old-space-size=1024"
npm run build 2>&1 || {{
  echo ">>> Build failed, retrying with more memory..."
  export NODE_OPTIONS="--max-old-space-size=1536"
  npm run build
}}
echo ">>> Build output:"
find dist/ -type f -name "*.js" -o -name "*.mjs" 2>/dev/null | head -20
find .output/ -type f -name "*.js" -o -name "*.mjs" 2>/dev/null | head -20
""", timeout=600)

    print(">>> Writing server-wrapper.mjs...")
    write_frontend_wrapper(client)

    print(">>> Restarting frontend service...")
    run(client, """
set -euo pipefail
systemctl restart agent-black-frontend
sleep 3
echo "=== Frontend Status ==="
systemctl is-active agent-black-frontend
echo ""
echo "=== Last 20 logs ==="
journalctl -u agent-black-frontend --no-pager -n 20
echo ""
echo "=== Health check ==="
curl -s -o /dev/null -w "Frontend: %{http_code}" http://127.0.0.1:3000/
echo ""
curl -s -o /dev/null -w "HTTPS: %{http_code}" https://agentblack.hareeshworks.in/
echo ""
""", timeout=30)


# ─── Main Menu ────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  AGENT BLACK v2 - SERVER DEPLOYER")
    print("  Fixes: data preservation + dynamic SSR entry")
    print("=" * 60)
    print(f"  Server : {USER}@{HOST}")
    print(f"  Domain : {DOMAIN}")
    print("=" * 60)
    print()
    print("  1) setup      - Full deploy")
    print("  2) status     - Check status")
    print("  3) update     - Upload code & restart (preserves data)")
    print("  4) restart    - Restart services")
    print("  5) logs       - View logs")
    print("  6) ssl-renew  - Renew SSL")
    print("  7) resetup    - WIPE everything & fresh install")
    print("  8) fix-ssr    - Rebuild frontend & fix SSR error")
    print()

    if len(sys.argv) > 1:
        choice = sys.argv[1].strip()
    else:
        choice = input("  Enter choice (1-8): ").strip()

    actions = {
        "1": ("setup", setup),
        "2": ("status", check_status),
        "3": ("update", update_version),
        "4": ("restart", restart_services),
        "5": ("logs", view_logs),
        "6": ("ssl-renew", renew_ssl),
        "7": ("resetup", resetup),
        "8": ("fix-ssr", fix_ssr),
    }
    if choice not in actions:
        print("  Invalid choice.")
        return

    name, fn = actions[choice]
    print(f"\n  Running: {name} ...\n")
    client = connect()
    fn(client)
    client.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
