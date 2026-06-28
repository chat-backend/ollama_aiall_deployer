# core/auto_drain.py

#!/usr/bin/env python3
"""
Auto-drain & auto-scale module for AIALL Gateway Cluster.

Nhiệm vụ chính:
- Đọc danh sách backend hiện tại
- Health-check backend (ưu tiên CLI cho node local)
- Đọc CPU metrics từ Node Exporter
- Tự động drain/undrain backend theo CPU
- Tự động scale-out / scale-in backend phụ (127.0.0.1:11435)
"""

import subprocess
from pathlib import Path
from typing import Tuple, Optional, List

from core.backends import (
    load_backends,
    load_drain_list,
    drain_backend,
    undrain_backend,
    add_backend,
    remove_backend,
)

# ============================================================
#  PATHS & STATE
# ============================================================

LOG_FILE = Path("/var/log/ollama-auto-drain.log")
STATE_DIR = Path("/var/lib/ollama-auto-drain")
SCALE_STATE_DIR = Path("/var/lib/ollama-auto-scale")

# Thresholds
CPU_DRAIN_THRESHOLD = 85
CPU_UNDRAIN_THRESHOLD = 60

CPU_SCALE_OUT_THRESHOLD = 90
CPU_SCALE_IN_THRESHOLD = 30

# Max scale-out nodes
MAX_SCALE_OUT = 1


def ensure_state_dirs() -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        SCALE_STATE_DIR.mkdir(parents=True, exist_ok=True)
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Không để lỗi filesystem phá vỡ auto-drain
        pass


# ============================================================
#  LOGGING
# ============================================================

def log(msg: str) -> None:
    line = f"[DRAIN] {msg}"
    print(line)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        # Logging không được phép làm hỏng logic chính
        pass


# ============================================================
#  METRICS / CPU PARSING
# ============================================================

def curl_metrics(url: str) -> Optional[str]:
    try:
        out = subprocess.check_output(
            ["curl", "-fsS", "--max-time", "2", url],
            stderr=subprocess.DEVNULL,
        )
        return out.decode()
    except Exception:
        return None


def parse_cpu(metrics: str) -> Tuple[float, float]:
    idle = 0.0
    busy = 0.0
    for line in metrics.splitlines():
        if "node_cpu_seconds_total" not in line:
            continue
        if 'mode="idle"' in line:
            idle += float(line.split()[-1])
        elif 'mode="' in line:
            busy += float(line.split()[-1])
    return idle, busy


# ============================================================
#  CPU STATE / PERCENT
# ============================================================

def load_cpu_state(host: str) -> Optional[Tuple[float, float]]:
    state_file = STATE_DIR / f"cpu_{host}.state"
    if not state_file.exists():
        return None
    try:
        prev_idle, prev_busy = map(float, state_file.read_text().split())
        return prev_idle, prev_busy
    except Exception:
        return None


def save_cpu_state(host: str, idle: float, busy: float) -> None:
    state_file = STATE_DIR / f"cpu_{host}.state"
    try:
        state_file.write_text(f"{idle} {busy}")
    except Exception:
        pass


def compute_cpu_percent(host: str, idle: float, busy: float) -> Optional[int]:
    prev = load_cpu_state(host)
    save_cpu_state(host, idle, busy)

    if prev is None:
        log(f"Init CPU state for {host}")
        return None

    prev_idle, prev_busy = prev
    delta_idle = idle - prev_idle
    delta_busy = busy - prev_busy
    delta_total = delta_idle + delta_busy

    if delta_total <= 0:
        return None

    cpu_percent = int((delta_busy / delta_total) * 100)
    return cpu_percent


# ============================================================
#  SCALE STATE
# ============================================================

def load_scale_count(host: str) -> int:
    scale_file = SCALE_STATE_DIR / f"scale_{host}.state"
    if not scale_file.exists():
        return 0
    try:
        return int(scale_file.read_text().strip())
    except Exception:
        return 0


def save_scale_count(host: str, count: int) -> None:
    scale_file = SCALE_STATE_DIR / f"scale_{host}.state"
    try:
        scale_file.write_text(str(count))
    except Exception:
        pass


# ============================================================
#  HEALTH CHECK (CLI-BASED FOR LOCAL NODE)
# ============================================================

def cli_health(timeout: int = 3) -> bool:
    """
    Health-check cho Ollama 0.30.x bằng CLI:
    - `ollama ps` trả về exit code = 0 nếu daemon healthy
    - Áp dụng cho node local (127.0.0.1 / localhost)
    """
    try:
        result = subprocess.run(
            ["/usr/local/bin/ollama", "ps"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            check=True,
        )
        return result.returncode == 0
    except Exception:
        return False


# ============================================================
#  AUTO-DRAIN / AUTO-SCALE LOGIC
# ============================================================

def process_backend(backend: str, backends: List[str], drains: List[str]) -> None:
    host, port = backend.split(":")
    metrics_url = f"http://{host}:9100/metrics"

    # HEALTH CHECK (local node ưu tiên CLI)
    if host in ("127.0.0.1", "localhost"):
        if not cli_health():
            log(f"{backend} unhealthy (CLI) → draining")
            drain_backend(backend)
            return

    # METRICS CHECK
    metrics = curl_metrics(metrics_url)
    if not metrics:
        log(f"Node Exporter unreachable for {backend} → draining")
        drain_backend(backend)
        return

    idle, busy = parse_cpu(metrics)
    cpu_percent = compute_cpu_percent(host, idle, busy)
    if cpu_percent is None:
        return

    log(f"{backend} CPU≈{cpu_percent}%")

    # AUTO-DRAIN
    if cpu_percent >= CPU_DRAIN_THRESHOLD:
        if backend not in drains:
            log(f"High load → draining {backend}")
            drain_backend(backend)

    elif cpu_percent <= CPU_UNDRAIN_THRESHOLD:
        if backend in drains:
            log(f"CPU normal → undraining {backend}")
            undrain_backend(backend)

    # AUTO-SCALE
    count = load_scale_count(host)

    # SCALE OUT
    if cpu_percent >= CPU_SCALE_OUT_THRESHOLD:
        count += 1
        save_scale_count(host, count)

        if count >= 3:
            current = [b for b in backends if b.startswith("127.0.0.1:11435")]
            if len(current) < MAX_SCALE_OUT:
                log("Scale-out triggered → adding backend 127.0.0.1:11435")
                add_backend("127.0.0.1:11435")
            else:
                log("Scale-out skipped (max reached)")
            save_scale_count(host, 0)

    # SCALE IN
    elif cpu_percent <= CPU_SCALE_IN_THRESHOLD:
        count += 1
        save_scale_count(host, count)

        if count >= 3:
            if "127.0.0.1:11435" in backends:
                log("Scale-in triggered → removing backend 127.0.0.1:11435")
                remove_backend("127.0.0.1:11435")
            save_scale_count(host, 0)

    else:
        save_scale_count(host, 0)


# ============================================================
#  MAIN ENTRY
# ============================================================

def auto_drain() -> None:
    """
    One-shot auto-drain/auto-scale:
    - Bỏ qua single-backend mode
    - Xử lý từng backend theo CPU & health
    """
    ensure_state_dirs()

    backends = load_backends()
    drains = load_drain_list()

    if len(backends) == 1:
        log("Single-backend mode — skip auto-drain/scale")
        return

    for backend in backends:
        process_backend(backend, backends, drains)


if __name__ == "__main__":
    auto_drain()
