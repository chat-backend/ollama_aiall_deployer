# config.py
#!/usr/bin/env python3
"""
Ollama PRO+ Gateway – System Configuration (V15)
------------------------------------------------

File cấu hình lõi của hệ thống Ollama PRO+ Gateway.
Được thiết kế để chạy 24/7 trên server Linux, đồng bộ hoàn toàn với:

- deploy_main.py V15
- nginx.py
- backends.py
- firewall.py
- monitoring.py
- backup.py
- system_services.py

Giữ nguyên chuẩn hệ thống:
- /etc/ollama
- /etc/nginx/conf.d
- /var/log
- Certbot
- Cron backup
- Systemd

Không phụ thuộc .env — vì đây là cấu hình hệ thống, không phải cấu hình ứng dụng.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import List


# ============================================================
#  DOMAIN & EMAIL CONFIG
# ============================================================

# Domain chính mà Gateway quản lý
DOMAINS: List[str] = [
    "api.aiallplatform.com",
]

# Email dùng cho Certbot (bắt buộc)
EMAIL: str = "openaimanage@gmail.com"


# ============================================================
#  BASE DIRECTORIES (CHUẨN HỆ THỐNG)
# ============================================================

CONFIG_DIR = Path("/etc/ollama")
CONFIG_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
#  PROJECT CONFIG FILES
# ============================================================

PROJECT_CONFIG_FILE = CONFIG_DIR / "project.conf"
API_KEY_FILE = CONFIG_DIR / "api_key"

BACKENDS_CONFIG = CONFIG_DIR / "backends.conf"
DRAIN_CONFIG = CONFIG_DIR / "backends.drain"

# Backend mặc định (Ollama local)
DEFAULT_BACKENDS = ["127.0.0.1:11434"]


# ============================================================
#  NGINX CONFIG PATHS
# ============================================================

UPSTREAM_FILE = Path("/etc/nginx/conf.d/ollama-upstream.conf")
LOG_FILE = Path("/var/log/ollama-deploy.log")


# ============================================================
#  PROJECT CONFIG STRUCTURE (Ollama Cloud Gateway v12)
# ============================================================

@dataclass
class ProjectConfig:
    """
    Cấu hình chuẩn Ollama Cloud Gateway V12.

    API chuẩn:
        https://domain/api/v12/chat/stream
        https://domain/api/v12/chat
        https://domain/api/v12/pull
        https://domain/api/v12/health

    File project.conf sẽ chứa:
        CONFIG_VERSION=1.0
        BASE_URL=https://domain
        API_GENERATE=...
        API_COMPLETION=...
        API_PULL=...
        API_HEALTH=...
        API_KEY=...
        TOKEN_SECRET=...
    """

    config_version: str = "1.0"

    # Domain gốc
    base_url: str = "https://api.aiallplatform.com"

    # API endpoints chuẩn V12
    api_generate: str = "/api/v12/chat/stream"
    api_completion: str = "/api/v12/chat"
    api_pull: str = "/api/v12/pull"
    api_health: str = "/api/v12/health"

    # Security
    api_key: str = ""
    token_secret: str = ""

    @staticmethod
    def from_dict(data: dict) -> "ProjectConfig":
        """Tạo ProjectConfig từ file project.conf"""
        return ProjectConfig(
            config_version=data.get("CONFIG_VERSION", "1.0"),
            base_url=data.get("BASE_URL", "https://api.aiallplatform.com"),

            api_generate=data.get("API_GENERATE", "/api/v12/chat/stream"),
            api_completion=data.get("API_COMPLETION", "/api/v12/chat"),
            api_pull=data.get("API_PULL", "/api/v12/pull"),
            api_health=data.get("API_HEALTH", "/api/v12/health"),

            api_key=data.get("API_KEY", ""),
            token_secret=data.get("TOKEN_SECRET", ""),
        )
