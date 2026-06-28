# gunicorn.conf.py
# AIALL Gateway – Production Gunicorn Configuration

import multiprocessing
import os

# ================================
#  Server Binding
# ================================
# Gunicorn chạy sau Nginx reverse proxy
bind = "0.0.0.0:5000"

# ================================
#  Worker Settings
# ================================
# Công thức chuẩn: CPU * 2 + 1
workers = multiprocessing.cpu_count() * 2 + 1

# Worker async – phù hợp API Gateway
worker_class = "gevent"

# Mỗi worker restart sau X request để tránh memory leak
max_requests = 2000
max_requests_jitter = 200

# ================================
#  Performance Tuning
# ================================
timeout = 120
graceful_timeout = 30
keepalive = 5
worker_connections = 2000  # gevent concurrency

# ================================
#  Logging
# ================================
loglevel = "info"
accesslog = "/var/log/aiall-gateway-access.log"
errorlog = "/var/log/aiall-gateway-error.log"

# Format log đẹp hơn
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s '
    '"%(f)s" "%(a)s"'
)

# ================================
#  Security Hardening
# ================================
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# Không cho client gửi body quá lớn (16MB)
limit_request_body = 16 * 1024 * 1024

# ================================
#  Reload (Dev Mode)
# ================================
# Tự bật reload nếu chạy local dev
reload = os.getenv("APP_ENV") == "development"

# ================================
#  Preload App
# ================================
# Tăng tốc khởi động worker
preload_app = True
