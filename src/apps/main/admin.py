from django.contrib import admin
from reversion.admin import VersionAdmin

from utils.admin import JsonMixin

from .models import (
    Quest,
    RawEventLog,
    ParsedEventLog,
    Balance,
    BalanceLog,
    UserBalance,
    ScoreLog,
    UsersCommand,
    CommandBalance,
    IndividualChallenge,
    IndividualChallengeRequest,
    CommandChallenge,
    CommandChallengeRequest,
    Achievement,
    UserAchievement,
)


@admin.register(Quest)
class QuestAdmin(JsonMixin, VersionAdmin):
    ...


@admin.register(RawEventLog)
class RawEventLogAdmin(JsonMixin, admin.ModelAdmin):
    ...


@admin.register(ParsedEventLog)
class ParsedEventLogAdmin(JsonMixin, admin.ModelAdmin):
    ...


@admin.register(Balance)
class BalanceAdmin(JsonMixin, admin.ModelAdmin):
    ...


@admin.register(BalanceLog)
class BalanceLogAdmin(JsonMixin, admin.ModelAdmin):
    ...


@admin.register(UserBalance)
class UserBalanceAdmin(JsonMixin, admin.ModelAdmin):
    ...


@admin.register(ScoreLog)
class ScoreLogAdmin(JsonMixin, admin.ModelAdmin):
    ...


@admin.register(UsersCommand)
class UsersCommandAdmin(VersionAdmin):
    ...


@admin.register(CommandBalance)
class CommandBalanceAdmin(JsonMixin, admin.ModelAdmin):
    ...


@admin.register(CommandChallenge)
class CommandChallengeAdmin(VersionAdmin):
    ...


@admin.register(CommandChallengeRequest)
class CommandChallengeRequestAdmin(VersionAdmin):
    ...


@admin.register(IndividualChallenge)
class IndividualChallengeAdmin(VersionAdmin):
    ...


@admin.register(IndividualChallengeRequest)
class IndividualChallengeRequestAdmin(VersionAdmin):
    ...


@admin.register(Achievement)
class AchievementAdmin(JsonMixin, VersionAdmin):
    ...


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    ...
