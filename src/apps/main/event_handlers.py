from .models import (
    ParsedEventLog,
)


class DocCompletedHandler:
    def handle(self, event: ParsedEventLog):
        ...


class NewUserHandler:
    def handle(self, event: ParsedEventLog):
        ...


class WorkStartHandler:
    def handler(self, event: ParsedEventLog):
        ...


class WorkStopHandler:
    def handler(self, event: ParsedEventLog):
        ...


class WorkFinishHandler:
    def handler(self, event: ParsedEventLog):
        ...


handlers = {
    'doc completed': DocCompletedHandler,
    'new user': NewUserHandler,
    'work start': WorkStartHandler,
    'work stop': WorkStopHandler,
    'work finish': WorkFinishHandler,
}
