from django.db import models
from django_json_widget.widgets import JSONEditorWidget


class JsonMixin:
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }
