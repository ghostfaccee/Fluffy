from celery import Celery

from app.core import env_settings

celery_app = Celery(
    'fluffy',
    broker = env_settings.RABBITMQ_URL,
    include = [
        'app.tasks.email',
        'app.tasks.login_code'
    ]
)

celery_app.conf.update(
    task_serializer = 'json',
    accept_content = ['json'],
    result_serializer = 'json',
    timezone = 'UTC',
    enable_utc = True,

    task_acks_late = True,
    task_reject_on_worker_lost = True,
    worker_prefetch_multiplier = 1,

    task_ignore_result = True
)
