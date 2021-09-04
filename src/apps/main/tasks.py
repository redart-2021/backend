import logging

from django.db import transaction

from conf.celery_app import app
from .models import (
    RawEventLog,
    ParsedEventLog,
)
from .event_parsers import parsers
from .event_handlers import handlers

logger = logging.getLogger(__name__)


@app.task(bind=True)
def parse_event(self, event: RawEventLog):
    event.lock()

    parser = parsers.get(event.content_type)
    if not parser:
        event.fail()
        return

    try:
        parsed_events = parser().parse(event.raw_data)
    except Exception:
        event.fail()
        return

    with transaction.atomic():
        event.success()
        to_create = [
            ParsedEventLog(
                raw_log=event,
                parsed_data=parsed_event,
            )
            for parsed_event in parsed_events
        ]
        ParsedEventLog.objects.bulk_create(to_create)

    for parsed in to_create:
        handle_event(parsed)


@app.task(bind=True)
def handle_event(self, event: ParsedEventLog):
    event.lock()

    handler = handlers.get(event.parsed_data.get('type'))
    if not handler:
        event.fail()
        return

    try:
        handler().handle(event.parsed_data)
    except Exception:
        event.fail()
        return

    event.success()
