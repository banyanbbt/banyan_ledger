from celery.schedules import crontab

from celery_tasks import settings

broker_url = settings.BROKER_URL
result_backend = settings.RESULT_BACKEND

imports = [
    'celery_tasks.phb.tasks'
]

beat_schedule = {
    "tasks": {
        "task": "celery_tasks.phb.tasks.post_hpb",
        "schedule":crontab(minute=0,hour="*")
        # "schedule": crontab(minute="*/1")
    }
}
