from __future__ import absolute_import, unicode_literals
import os
from celery import Celery


# celery -A emptyClassroom worker --pool=solo --loglevel=info

# Set default Django settings module for Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emptyClassroom.settings')

app = Celery('emptyClassroom')

# Use Django's settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in installed apps
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')