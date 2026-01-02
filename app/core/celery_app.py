"""
Setup Celery app with Redis broker and optional MSSQL result backend.
Set USE_DB=true to enable MSSQL result backend.

> source venv/bin/activate
> source .env

> celery -A app.core.celery_app.celery_app worker --loglevel=info
> celery -A app.core.celery_app:celery_app worker -Q statment_parser,celery --loglevel=info  --events
"""

import logging

from celery import Celery
from celery.backends.database.models import TaskExtended, TaskSet
from celery.schedules import crontab
from sqlalchemy import BigInteger, create_engine

from app.config.settings import settings
from app.core.celery_signal import BaseTaskSignal

logger = logging.getLogger(__name__)

# engine = create_engine(
#     settings.CELERY_BACKEND_URL.replace(
#         "db+", ""
#     )  # Remove Celery prefix for SQLAlchemy
# )

# # Monkey patching only for MSSQL & json result wont work.
# # Mssql : https://github.com/celery/celery/issues/8634
# # https://github.com/celery/celery/milestone/44
# TaskExtended.__table__.c.id.type = BigInteger()
# TaskSet.__table__.c.id.type = BigInteger()
# TaskExtended.__table__.create(bind=engine, checkfirst=True)
# TaskSet.__table__.create(bind=engine, checkfirst=True)


# Initialize Celery
celery_app = Celery(
    "core",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_BACKEND_URL,
    task_track_started=True,
    result_extended=True,
)

celery_app.conf.timezone = "Asia/Kolkata"
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_accept_content=["json"],
    worker_send_task_events=True
)


# Schedule example
celery_app.conf.beat_schedule = {
    "daily-task": {
        "task": "app.tasks.clean_up.cleanup_resources",
        "schedule": crontab(hour="9-21", day_of_week="1-5"),
    },
}

celery_app.autodiscover_tasks(["app"], related_name="tasks")


@celery_app.task(name="app.core.celery_app.hello")
def hello():
    """Test function"""
    return "Hello from Celery!"


@celery_app.task(name="app.core.celery_app.add", base=BaseTaskSignal)
def add(x, y):
    """Test function"""
    return x + y
