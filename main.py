# main.py — FastAPI version (final)

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

from config_loader import load_runtime_config
import core.deploy_app as deploy

# Load config
cfg = load_runtime_config()

# Create FastAPI app
app = FastAPI(
    title="Ollama PRO+ Gateway",
    version="1.0.0",
)

# ============================
#  ROOT ENDPOINT
# ============================
@app.get("/")
def index():
    return {
        "status": "running",
        "base_url": cfg.base_url
    }

# ============================
#  HEALTH CHECK
# ============================
@app.get("/health")
def health():
    return {"status": "ok"}

# ============================
#  DEPLOY ENDPOINT
# ============================
@app.get("/deploy")
def deploy_now():
    deploy.full_deploy()
    return {"status": "deploy completed"}

# ============================
#  INFO ENDPOINT
# ============================
@app.get("/api/v1/info")
def info():
    return {
        "service": "Ollama Gateway",
        "version": "1.0.0",
        "base_url": cfg.base_url
    }

# ============================
#  UVICORN ENTRY POINT
# ============================
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
