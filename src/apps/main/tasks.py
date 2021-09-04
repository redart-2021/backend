import logging

from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from apps.user.models import CustomUser
from conf.celery_app import app

logger = logging.getLogger(__name__)


@app.task(bind=True)
def some_task(self):
    ...
