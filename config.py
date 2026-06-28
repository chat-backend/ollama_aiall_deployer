# config.py
#!/usr/bin/env python3
"""
Ollama PRO+ Gateway – System Configuration (V15-FIXED)
------------------------------------------------------
Phiên bản đã chỉnh sửa theo đúng logic:
BASE_URL = https://api.aiallplatform.com
API phải đi qua prefix /ollama/ để kết nối mô hình Ollama.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import List

print("[CONFIG] Loaded Ollama PRO+ Gateway configuration (V15-FIXED)")

# ============================================================
#  DOMAIN & EMAIL CONFIG
# ============================================================

DOMAINS: List[str] = ["api.aiallplatform.com"]
EMAIL: str = "openaimanage@gmail.com"

# ============================================================
#  BASE DIRECTORIES
# ============================================================

CONFIG_DIR = Path("/etc/ollama")
try:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
except PermissionError:
    print("[WARN] Không thể tạo /etc/ollama — hãy chạy bằng sudo.")

# ============================================================
#  PROJECT CONFIG FILES
# ============================================================

PROJECT_CONFIG_FILE = CONFIG_DIR / "project.conf"
API_KEY_FILE = CONFIG_DIR / "api_key"
BACKENDS_CONFIG = CONFIG_DIR / "backends.conf"
DRAIN_CONFIG = CONFIG_DIR / "backends.drain"
DEFAULT_BACKENDS = ["127.0.0.1:11434"]

# ============================================================
#  NGINX CONFIG PATHS
# ============================================================

UPSTREAM_FILE = Path("/etc/nginx/conf.d/ollama-upstream.conf")
LOG_FILE = Path("/var/log/ollama-deploy.log")

# ============================================================
#  PROJECT CONFIG STRUCTURE
# ============================================================

@dataclass
class ProjectConfig:
    config_version: str = "1.0"

    # Domain gốc
    base_url: str = "https://api.aiallplatform.com"

    # API đúng chuẩn Ollama (đã sửa)
    api_generate: str = "/ollama/api/generate"
    api_completion: str = "/ollama/api/generate"   # Ollama không có /completion riêng
    api_pull: str = "/ollama/api/pull"
    api_health: str = "/ollama/api/health"

    api_key: str = ""
    token_secret: str = ""

    @staticmethod
    def from_dict(data: dict) -> "ProjectConfig":
        return ProjectConfig(
            config_version=data.get("CONFIG_VERSION", "1.0"),
            base_url=data.get("BASE_URL", "https://api.aiallplatform.com"),

            # API đúng chuẩn Ollama
            api_generate=data.get("API_GENERATE", "/ollama/api/generate"),
            api_completion=data.get("API_COMPLETION", "/ollama/api/generate"),
            api_pull=data.get("API_PULL", "/ollama/api/pull"),
            api_health=data.get("API_HEALTH", "/ollama/api/health"),

            api_key=data.get("API_KEY", ""),
            token_secret=data.get("TOKEN_SECRET", ""),
        )

__all__ = [
    "DOMAINS",
    "EMAIL",
    "CONFIG_DIR",
    "PROJECT_CONFIG_FILE",
    "API_KEY_FILE",
    "BACKENDS_CONFIG",
    "DRAIN_CONFIG",
    "DEFAULT_BACKENDS",
    "UPSTREAM_FILE",
    "LOG_FILE",
    "ProjectConfig",
]

