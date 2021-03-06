from django.db import models
from django.utils import timezone

from utils.models import (
    AdditionalDataMixin,
    CommentMixin,
    CreatedAtMixin,
    NameMixin,
)


class LogMixin(CreatedAtMixin, AdditionalDataMixin, CommentMixin):
    class Meta:
        abstract = True


class RawEventLog(CreatedAtMixin, AdditionalDataMixin):
    raw_data = models.BinaryField(verbose_name='Оригинальное сообщение')
    content_type = models.CharField(max_length=255, null=True, blank=True, verbose_name='Тип')
    locked_by = models.CharField(max_length=255, null=True, blank=True, verbose_name='Кем залочен')
    locked_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата-время лока')
    parsed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата-время разбора')
    parse_failed = models.BooleanField(default=False, verbose_name='Ошибка разбора')

    class Meta:
        verbose_name = 'Сырой входящий лог'
        verbose_name_plural = 'Сырые входящие логи'

    def lock(self, locker=None):
        self.locked_at = timezone.now()
        self.locked_by = locker
        self.save()

    def fail(self):
        self.parsed_at = timezone.now()
        self.parse_failed = True
        self.save()

    def success(self):
        self.parsed_at = timezone.now()
        self.save()


# todo: подразделение


class ParsedEventLog(CreatedAtMixin):
    raw_log = models.ForeignKey('RawEventLog', on_delete=models.CASCADE, verbose_name='Сырой лог')
    parsed_data = models.JSONField(default=dict, verbose_name='Обработанные данные')
    locked_by = models.CharField(max_length=255, null=True, blank=True, verbose_name='Кем залочен')
    locked_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата-время лока')
    handled_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата-время выполнения')
    handle_failed = models.BooleanField(default=False, verbose_name='Ошибка выполнения')

    class Meta:
        verbose_name = 'Обработанный входящий лог'
        verbose_name_plural = 'Обработанные входящие логи'
        default_related_name = 'parsed_event_logs'

    def lock(self, locker=None):
        self.locked_at = timezone.now()
        self.locked_by = locker
        self.save()

    def fail(self):
        self.handled_at = timezone.now()
        self.handle_failed = True
        self.save()

    def success(self):
        self.handled_at = timezone.now()
        self.save()


class Balance(AdditionalDataMixin):
    amount = models.PositiveBigIntegerField(verbose_name='Баллы')
    frozen = models.PositiveBigIntegerField(verbose_name='Замороженные баллы')

    class Meta:
        verbose_name = 'Баланс'
        verbose_name_plural = 'Балансы'


class BalanceLog(LogMixin):
    # source: quest | challenge
    balance = models.ForeignKey('Balance', on_delete=models.CASCADE, verbose_name='Баланс')
    amount = models.BigIntegerField(verbose_name='Дельта общего количество баллов')
    frozen = models.BigIntegerField(verbose_name='Дельта замороженного количество баллов')

    class Meta:
        verbose_name = 'Лог баланса'
        verbose_name_plural = 'Логи балансов'
        default_related_name = 'logs'


class UserBalance(AdditionalDataMixin):
    user = models.OneToOneField('user.CustomUser', on_delete=models.CASCADE,
                                verbose_name='Пользователь')
    balance = models.OneToOneField('Balance', on_delete=models.CASCADE, verbose_name='Баланс')

    class Meta:
        verbose_name = 'Актуальный баланс пользователя'
        verbose_name_plural = 'Актуальные балансы пользователей'
        default_related_name = 'user_balance'


class ScoreLog(LogMixin):
    # source: quest | challenge
    user = models.ForeignKey('user.CustomUser', on_delete=models.CASCADE,
                             verbose_name='Пользователь')
    score = models.BigIntegerField(verbose_name='Дельта очков')

    class Meta:
        verbose_name = 'Лог рейтинга'
        verbose_name_plural = 'Логи рейтинга'
        default_related_name = 'score_logs'


class Quest(NameMixin, CreatedAtMixin, AdditionalDataMixin):
    # reversion
    description = models.TextField(verbose_name='Описание')
    reward = models.BigIntegerField(verbose_name='Очки награды')
    valid_from = models.DateTimeField(null=True, blank=True, verbose_name='Действует с')
    valid_to = models.DateTimeField(null=True, blank=True, verbose_name='Действует до')

    class Meta:
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'


class UsersCommand(NameMixin):
    # reversion
    description = models.TextField(verbose_name='Описание')
    users = models.ManyToManyField('user.CustomUser', blank=True)

    class Meta:
        verbose_name = 'Команда (пользователи)'
        verbose_name_plural = 'Команда (пользователи)'
        default_related_name = 'users_commands'


class CommandBalance(AdditionalDataMixin):
    command = models.ForeignKey('UsersCommand', on_delete=models.CASCADE,
                                verbose_name='Команда')
    balance = models.OneToOneField('Balance', on_delete=models.CASCADE, verbose_name='Баланс')

    class Meta:
        verbose_name = 'Актуальный баланс команды'
        verbose_name_plural = 'Актуальные балансы команд'
        default_related_name = 'command_balances'


class IndividualChallenge(NameMixin):
    # reversion
    description = models.TextField(verbose_name='Описание')
    creator = models.ForeignKey('user.CustomUser', on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='Создатель')
    quest = models.ForeignKey('Quest', on_delete=models.CASCADE, verbose_name='Задание')
    start_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата-время начала')
    finish_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата-время конца')
    is_private = models.BooleanField(default=False, verbose_name='Приватное')

    class Meta:
        verbose_name = 'Соревнование индивидуальное'
        verbose_name_plural = 'Соревнования индивидуальные'
        default_related_name = 'individual_challenges'


class IndividualChallengeRequest(CreatedAtMixin):
    # reversion
    challenge = models.ForeignKey('IndividualChallenge', on_delete=models.CASCADE,
                                  related_name='requests', verbose_name='Соревновие')
    member = models.ForeignKey('user.CustomUser', on_delete=models.CASCADE,
                               verbose_name='Участник')
    # rejected by owner, rejected by member, accepted
    answer = models.CharField(max_length=50, null=True, blank=True, verbose_name='Ответ')
    answered_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата-время ответа')

    class Meta:
        verbose_name = 'Заявка на участие в индивидуальном соревновании'
        verbose_name_plural = 'Заявки на участие в индивидуальном соревновании'
        default_related_name = 'individual_challenges_requests'


class CommandChallenge(NameMixin):
    # reversion
    description = models.TextField(verbose_name='Описание')
    creator = models.ForeignKey('user.CustomUser', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='requests', verbose_name='Создатель')
    quest = models.ForeignKey('Quest', on_delete=models.CASCADE, verbose_name='Задание')
    start_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата-время начала')
    finish_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата-время конца')
    is_private = models.BooleanField(default=False, verbose_name='Приватное')

    class Meta:
        verbose_name = 'Соревнование командное'
        verbose_name_plural = 'Соревнования командные'
        default_related_name = 'command_challenges'


class CommandChallengeRequest(CreatedAtMixin):
    # reversion
    challenge = models.ForeignKey('CommandChallenge', on_delete=models.CASCADE,
                                  related_name='requests', verbose_name='Соревновие')
    member = models.ForeignKey('UsersCommand', on_delete=models.CASCADE,
                               verbose_name='Участник')
    # rejected by owner, rejected by member, accepted
    answer = models.CharField(max_length=50, null=True, blank=True, verbose_name='Ответ')
    answered_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата-время ответа')

    class Meta:
        verbose_name = 'Заявка на участие в коммандном соревновании'
        verbose_name_plural = 'Заявки на участие в коммандном соревновании'
        default_related_name = 'command_challenges_requests'


class Achievement(NameMixin, CreatedAtMixin, AdditionalDataMixin):
    description = models.TextField(verbose_name='Описание')
    image = models.FileField(verbose_name='Картинка')

    class Meta:
        verbose_name = 'Достижение'
        verbose_name_plural = 'Достижения'


class UserAchievement(CreatedAtMixin):
    user = models.ForeignKey('user.CustomUser', on_delete=models.CASCADE)
    achievement = models.ForeignKey('Achievement', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Выданное достижение'
        verbose_name_plural = 'Выданные достижения'
        default_related_name = 'achievements'
