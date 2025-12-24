from __future__ import absolute_import, unicode_literals
import os
from celery.schedules import crontab
from celery import Celery
from django.core.mail import send_mail
from celery import shared_task

from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HRMS_PAYROLL.settings')
broker = os.environ.get('CELERY_BROKER_URL','redis://localhost:6380/0')
backend = os.environ.get('CELERY_RESULT_BACKEND','redis://localhost:6380/0')

app = Celery('HRMS_PAYROLL', broker=broker, backend=backend)
# app.config_from_object(__name__)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.enable_utc = False
app.conf.update(
    timezone='Asia/Kolkata',
    broker_connection_retry_on_startup=True,
    worker_max_restart_rate=10,  # Allow up to 10 restarts per minute
)

# Define the beat schedule
app.conf.beat_schedule = {
    
    'check-leave-pending-requests': {
        'task': 'payrollapp.tasks.checkpending',
        'schedule': crontab(minute="0"),
    },
    'subs_status': {
        'task': 'payrollapp.tasks.checksubstatus',
        'schedule': crontab(hour='00', minute='01'),
    },
    'updateleaves': {
        'task': 'payrollapp.tasks.update_leaves',
        'schedule': crontab(hour='00', minute='01'),
    },
    'greet': {
        'task': 'payrollapp.tasks.send_greeting',
        'schedule': crontab(hour='00', minute='01'),
    },
    'quote': {
        'task': 'payrollapp.tasks.GenerateQuote',
        'schedule': crontab(hour='00', minute='01'),
    },
    'calculateattendance': {
        'task': 'payrollapp.tasks.calculate_attendance',
        'schedule': crontab(hour='00', minute='01'),
    },
    'updateProfile': {
        'task': 'payrollapp.tasks.TriggerEmail',
        'schedule': crontab(hour='00', minute='01'),
    },
    'triggerDailyLogin': {
        'task': 'payrollapp.tasks.TriggerDailyLogin',
        'schedule': crontab(hour='09', minute='30'),
    },
    'notifyleave': {
        'task': 'payrollapp.tasks.notifyleave',
        'schedule': crontab(hour='12', minute='30'),
    },
    'notifyleave2': {
        'task': 'payrollapp.tasks.notifyleave',
        'schedule': crontab(hour='8', minute='30'),
    },
    'notifyleave3': {
        'task': 'payrollapp.tasks.notifyleave',
        'schedule': crontab(hour='15', minute='30'),
    },
    'notifyleave4': {
        'task': 'payrollapp.tasks.notifyleave',
        'schedule': crontab(hour='18', minute='30'),
    },
    'send-greetings': {
        'task': 'payrollapp.tasks.send_greeting',
        'schedule': crontab(hour=0, minute=1),    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request}')
# document verification
