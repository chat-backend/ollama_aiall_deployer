# main.py — FastAPI version (final)

#!/usr/bin/env python3
"""
Ollama PRO+ Gateway – System Service (Minimal Version)
------------------------------------------------------
Phiên bản này KHÔNG xử lý API chính.
API chính chạy qua Nginx → Ollama backend.
FastAPI chỉ cung cấp thông tin hệ thống (tùy chọn).
"""

from fastapi import FastAPI
import uvicorn

from config_loader import load_runtime_config

# Load config
cfg = load_runtime_config()

# Create FastAPI app
app = FastAPI(
    title="Ollama PRO+ System Service",
    version="1.0.0",
)

# ============================
#  ROOT ENDPOINT
# ============================
@app.get("/")
def index():
    return {
        "service": "Ollama PRO+ System Service",
        "status": "running",
        "note": "API chính chạy qua /ollama/api/... (Nginx → Ollama)",
        "base_url": cfg.base_url
    }

# ============================
#  HEALTH CHECK (SYSTEM ONLY)
# ============================
@app.get("/system/health")
def system_health():
    return {"status": "ok"}

# ============================
#  UVICORN ENTRY POINT
# ============================
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=6001,
        reload=False
    )
