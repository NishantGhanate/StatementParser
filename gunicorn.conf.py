# gunicorn.conf.py
import multiprocessing
import os

bind = f"0.0.0.0:{os.getenv('PORT', 8000)}"
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"

accesslog = "-"
errorlog = "-"
loglevel = os.getenv('LOG_LEVEL', 'info')

timeout = int(os.getenv('GUNICORN_TIMEOUT', 120))
keepalive = 5
graceful_timeout = 30

max_requests = 1000
max_requests_jitter = 50
