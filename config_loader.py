# config_loader.py
#!/usr/bin/env python3
"""
Runtime Config Loader for Ollama PRO+ Gateway (V15)
--------------------------------------------------

Dùng cho ứng dụng (app.py) để đọc cấu hình thật từ hệ thống:

- /etc/ollama/project.conf
- /etc/ollama/api_key

Không phụ thuộc .env.
Không dùng giá trị cố định.
Luôn lấy API_KEY và TOKEN_SECRET mới nhất.
"""

from pathlib import Path
from typing import Dict
from config import PROJECT_CONFIG_FILE, API_KEY_FILE, ProjectConfig


# ============================================================
#  LOAD project.conf
# ============================================================

def load_project_conf() -> Dict[str, str]:
    """Đọc file /etc/ollama/project.conf và trả về dict."""
    if not PROJECT_CONFIG_FILE.exists():
        raise FileNotFoundError(f"Missing project config: {PROJECT_CONFIG_FILE}")

    data = {}
    for line in PROJECT_CONFIG_FILE.read_text().splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()

    if not data:
        raise ValueError("project.conf is empty or invalid")

    return data


# ============================================================
#  LOAD api_key
# ============================================================

def load_api_key() -> str:
    """Đọc file /etc/ollama/api_key và trả về API_KEY thật."""
    if not API_KEY_FILE.exists():
        raise FileNotFoundError(f"Missing API key file: {API_KEY_FILE}")

    content = API_KEY_FILE.read_text().strip()

    # Chỉ chấp nhận AIALL_API_KEY để tránh rối
    if "=" in content:
        name, key = content.split("=", 1)
        name = name.strip()
        key = key.strip()

        if name != "AIALL_API_KEY":
            raise ValueError(f"Unexpected key name in api_key file: {name}")

        return key

    # Trường hợp file chỉ chứa key trần (fallback)
    return content


# ============================================================
#  LOAD FULL RUNTIME CONFIG
# ============================================================

def load_runtime_config() -> ProjectConfig:
    """
    Trả về ProjectConfig hoàn chỉnh:
    - BASE_URL
    - API endpoints
    - API_KEY
    - TOKEN_SECRET
    """

    data = load_project_conf()
    api_key = load_api_key()

    # Ghi đè API_KEY từ file api_key
    data["API_KEY"] = api_key

    # Validate tối thiểu
    if "TOKEN_SECRET" not in data or not data["TOKEN_SECRET"]:
        raise ValueError("TOKEN_SECRET missing in project.conf")

    return ProjectConfig.from_dict(data)
