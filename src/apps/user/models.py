from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    external_id = models.CharField(max_length=255, null=True, blank=True,
                                   verbose_name='Внешний идентификатор')
    middle_name = models.CharField(verbose_name='Отчество', max_length=150, blank=True, null=True)
    name = models.CharField(verbose_name='Полное имя', max_length=300, blank=True, null=True,
                            editable=False)
    position = models.CharField(max_length=300, null=True, blank=True, verbose_name='Должность')
    settings = models.JSONField(default=dict, verbose_name='Персональные настройки')
    score = models.BigIntegerField(default=0, verbose_name='Очки рейтинга')

    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta(AbstractUser.Meta):
        default_related_name = 'users'

    def get_full_name(self) -> str:
        return f'{self.last_name or ""} {self.first_name or ""} {self.middle_name or ""}'.strip()

    def get_short_name(self) -> str:
        md = (self.middle_name[0] + '.') if self.middle_name else ''
        return f'{self.last_name or ""} {(self.first_name or "")[:1]}.{md}'

    def save(self, *args, **kwargs):
        self.name = self.get_full_name()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name or ''
