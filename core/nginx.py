# core/nginx.py
"""
Nginx Manager for AIALL Gateway
Quản lý upstream, SSL, site config và reload Nginx.
"""

import subprocess
from pathlib import Path

from config import (
    UPSTREAM_FILE,
    PROJECT_CONFIG_FILE,
    DOMAINS,
)

from core.backends import get_active_backends
from core.health_cluster import health_check


# ============================================================
#  UTILS
# ============================================================

def log(msg: str) -> None:
    print(f"[NGINX] {msg}")


def run(cmd: list[str], check: bool = True) -> None:
    log(f"RUN: {' '.join(cmd)}")
    subprocess.run(cmd, check=check)


def atomic_write(path: Path, content: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content)
    tmp.replace(path)


# ============================================================
#  LOAD PROJECT CONFIG
# ============================================================

def load_project_config() -> dict:
    if not PROJECT_CONFIG_FILE.exists():
        raise RuntimeError(f"Project config not found: {PROJECT_CONFIG_FILE}")

    data = {}
    for line in PROJECT_CONFIG_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()

    return data


# ============================================================
#  GENERATE UPSTREAM BLOCK
# ============================================================

def generate_upstream_block() -> None:
    backends = get_active_backends()

    if not backends:
        log("❌ No active backends available! Upstream will be empty.")
        content = (
            "upstream ollama_cluster {\n"
            "    least_conn;\n"
            "    # No active backends available\n"
            "}\n"
        )
        atomic_write(UPSTREAM_FILE, content)
        return

    lines = [
        "upstream ollama_cluster {",
        "    least_conn;",
    ]

    for be in backends:
        lines.append(f"    server {be} max_fails=3 fail_timeout=30s;")

    lines.append("}")

    atomic_write(UPSTREAM_FILE, "\n".join(lines) + "\n")
    log(f"Updated upstream with active backends: {', '.join(backends)}")


# ============================================================
#  BUILD NGINX SITE CONFIG
# ============================================================

def build_nginx_site_content(domain: str, api_key: str) -> str:
    return f"""
server {{
    listen 80;
    server_name {domain};
    return 301 https://$host$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {domain};

    ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    client_max_body_size 100M;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location / {{
        return 404;
    }}

    location /ollama/ {{

        if ($http_x_api_key = "") {{
            return 401;
        }}

        if ($http_x_api_key != "{api_key}") {{
            return 403;
        }}

        rewrite ^/ollama/(.*)$ /$1 last;

        proxy_pass http://ollama_cluster/;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_read_timeout 3600;
        proxy_send_timeout 3600;
        proxy_buffering off;
        proxy_request_buffering off;
    }}
}}
""".lstrip()


def configure_nginx_site_for_domain(domain: str) -> None:
    cfg = load_project_config()
    api_key = cfg.get("API_KEY", "")

    site_file = Path(f"/etc/nginx/sites-available/ollama-{domain}")
    atomic_write(site_file, build_nginx_site_content(domain, api_key))

    enabled = Path(f"/etc/nginx/sites-enabled/ollama-{domain}")
    enabled.parent.mkdir(parents=True, exist_ok=True)

    if enabled.exists() or enabled.is_symlink():
        enabled.unlink()

    enabled.symlink_to(site_file)

    log(f"Nginx site configured for {domain}")


# ============================================================
#  RELOAD NGINX
# ============================================================

def reload_nginx() -> None:
    log("Testing nginx config...")
    run(["nginx", "-t"])

    log("Reloading nginx...")
    run(["nginx", "-s", "reload"])


# ============================================================
#  ISSUE SSL
# ============================================================

def issue_ssl_for_domain(domain: str) -> None:
    log(f"Requesting SSL for {domain}")

    live_dir = Path(f"/etc/letsencrypt/live/{domain}")
    if live_dir.exists():
        log(f"SSL for {domain} already exists, skipping.")
        return

    run(["systemctl", "stop", "nginx"], check=False)

    run([
        "certbot", "certonly", "--standalone",
        "-d", domain,
        "--non-interactive",
        "--agree-tos",
        "-m", "openaimanage@gmail.com",
    ])

    log(f"SSL obtained for {domain}")


# ============================================================
#  FULL DEPLOY PIPELINE
# ============================================================

def configure_all_domains() -> None:
    log("=== Starting full Nginx/Ollama gateway deployment ===")

    log("Step 1: Running backend health-check...")
    health_check()

    log("Step 2: Generating upstream block...")
    generate_upstream_block()

    for domain in DOMAINS:
        log(f"--- Processing domain: {domain} ---")
        issue_ssl_for_domain(domain)
        configure_nginx_site_for_domain(domain)

    reload_nginx()
    log("=== Deployment completed successfully ===")
