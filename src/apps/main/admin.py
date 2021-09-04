from django.contrib import admin
from reversion.admin import VersionAdmin

from utils.admin import JsonMixin

from .models import (
    Quest,
)


@admin.register(Quest)
class QuestAdmin(VersionAdmin):
    ...
