# core//auto_update.py
#!/usr/bin/env python3
"""
Auto-update module for Ollama PRO+ Cluster (V15)
Compatible with Linux (full mode) and Windows (safe-skip mode)
"""

import os
import shutil
import subprocess
from time import sleep


# ============================================================
#  UTILS
# ============================================================
def log(msg: str) -> None:
    print(f"[AUTO-UPDATE] {msg}")


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """
    Safe wrapper for subprocess.run
    """
    log(f"RUN: {' '.join(cmd)}")
    try:
        return subprocess.run(cmd, check=check)
    except Exception as e:
        log(f"❌ Command failed: {e}")
        if check:
            raise
        return subprocess.CompletedProcess(cmd, 1)


def is_linux() -> bool:
    return os.name == "posix"


def is_linux_root() -> bool:
    if hasattr(os, "geteuid"):
        return os.geteuid() == 0
    return False


def require_root() -> None:
    if is_linux() and not is_linux_root():
        raise SystemExit("Please run as root (sudo).")


def check_internet() -> None:
    log("Checking internet connectivity...")

    ping_cmd = ["ping", "-n", "1", "8.8.8.8"] if os.name == "nt" else ["ping", "-c", "1", "8.8.8.8"]

    result = subprocess.run(
        ping_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if result.returncode != 0:
        log("❌ No internet connection — aborting update.")
        raise SystemExit(1)

    log("✅ Internet OK.")


# ============================================================
#  SYSTEM UPDATE
# ============================================================
def update_system() -> None:
    if not is_linux():
        log("Windows detected — skipping system update.")
        return

    apt = shutil.which("apt")
    if not apt:
        log("apt not found — skipping system update.")
        return

    log("Updating system packages...")

    run(["rm", "-f", "/var/lib/dpkg/lock-frontend"], check=False)
    run(["rm", "-f", "/var/lib/dpkg/lock"], check=False)

    run([apt, "update", "-y"])
    run([apt, "upgrade", "-y"])
    run([apt, "autoremove", "-y"])

    log("✅ System packages updated.")


# ============================================================
#  UPDATE OLLAMA
# ============================================================
def update_ollama() -> None:
    ollama_bin = shutil.which("ollama")
    if not ollama_bin:
        log("Ollama not installed — skipping.")
        return

    if not is_linux():
        log("Windows detected — skipping Ollama update.")
        return

    log("Updating Ollama (if new version available)...")

    run(["bash", "-c", "curl -fsSL https://ollama.com/install.sh | sh"], check=False)
    sleep(2)

    systemctl = shutil.which("systemctl")
    if systemctl:
        run([systemctl, "restart", "ollama"], check=False)
        log("Ollama restarted via systemctl.")
    else:
        log("systemctl not found — please restart Ollama manually.")


# ============================================================
#  UPDATE NGINX
# ============================================================
def update_nginx() -> None:
    nginx_bin = shutil.which("nginx")
    if not nginx_bin:
        log("Nginx not installed — skipping.")
        return

    log("Reloading Nginx...")

    test_result = run([nginx_bin, "-t"], check=False)
    if test_result.returncode == 0:
        run([nginx_bin, "-s", "reload"], check=False)
        log("✅ Nginx reloaded.")
    else:
        log("❌ Nginx config invalid — NOT reloading.")


# ============================================================
#  UPDATE NODE EXPORTER
# ============================================================
def update_node_exporter() -> None:
    node_exporter = shutil.which("node_exporter")
    if not node_exporter:
        log("Node Exporter not installed — skipping.")
        return

    log("Restarting Node Exporter...")

    systemctl = shutil.which("systemctl")
    if systemctl:
        run([systemctl, "restart", "node_exporter"], check=False)
        log("✅ Node Exporter restarted.")
    else:
        log("systemctl not found — please restart node_exporter manually.")


# ============================================================
#  UPDATE FAIL2BAN
# ============================================================
def update_fail2ban() -> None:
    fail2ban = shutil.which("fail2ban-client")
    if not fail2ban:
        log("Fail2ban not installed — skipping.")
        return

    log("Reloading Fail2ban...")

    systemctl = shutil.which("systemctl")
    if systemctl:
        run([systemctl, "reload", "fail2ban"], check=False)
        run([systemctl, "restart", "fail2ban"], check=False)
        log("✅ Fail2ban reloaded & restarted.")
    else:
        log("systemctl not found — please manage Fail2ban manually.")


# ============================================================
#  AUTO UPDATE MODE (FULL)
# ============================================================
def auto_update_mode() -> None:
    log("🚀 Starting AUTO-UPDATE mode...")

    require_root()
    check_internet()

    update_system()
    update_ollama()
    update_nginx()
    update_node_exporter()
    update_fail2ban()

    log("✅ AUTO-UPDATE completed successfully.")


