# main.py
#!/usr/bin/env python3
"""
AIALL Gateway – Runtime App (Flask)
Đọc cấu hình thật từ hệ thống thông qua config_loader.py
Không phụ thuộc .env – luôn đồng bộ với deploy_app.py
"""

from flask import Flask, jsonify
from config_loader import load_runtime_config
import os

app = Flask(__name__)

# Load cấu hình thật từ hệ thống
cfg = load_runtime_config()


@app.route("/")
def index():
    return jsonify({
        "app": "AIALL Gateway",
        "environment": "production",
        "base_url": cfg.base_url,
        "api_generate": cfg.api_generate,
        "api_completion": cfg.api_completion,
        "api_pull": cfg.api_pull,
        "api_health": cfg.api_health,
        "status": "running"
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/auth-info")
def auth_info():
    # Chỉ cho phép xem khi chạy local dev
    if os.getenv("APP_ENV") == "production":
        return jsonify({"error": "This endpoint is disabled in production"}), 403

    return jsonify({
        "api_key": cfg.api_key,
        "token_secret": cfg.token_secret,
        "note": "Debug only. Do NOT expose in production."
    })


if __name__ == "__main__":
    # Chạy dev mode – production dùng Gunicorn
    app.run(host="0.0.0.0", port=5000, debug=False)

