from django.db import models

__all__ = ['CreatedAtMixin', 'UpdatedAtMixin', 'NameMixin', 'OrderedMixin', 'AdditionalDataMixin',
           'CommentMixin']


class CreatedAtMixin(models.Model):
    created_at = models.DateTimeField(
        verbose_name='Дата-время создания', auto_now_add=True,
    )

    class Meta:
        abstract = True


class UpdatedAtMixin(models.Model):
    updated_at = models.DateTimeField(
        verbose_name='Дата-время изменения', auto_now=True,
    )

    class Meta:
        abstract = True


class NameMixin(models.Model):
    name = models.CharField(
        verbose_name='Название', max_length=250,
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class OrderedManager(models.Manager):
    @property
    def ordered_desc(self):
        return self.get_queryset().order_by('-order_num')

    @property
    def ordered_asc(self):
        return self.get_queryset().order_by('order_num')


class OrderedMixin(models.Model):
    order_num = models.PositiveIntegerField(
        verbose_name='Очередь', default=0,
    )

    class Meta:
        abstract = True

    objects = OrderedManager()


class AdditionalDataMixin(models.Model):
    additional_data = models.JSONField(default=dict, blank=True, verbose_name='Доп данные')

    class Meta:
        abstract = True


class CommentMixin(models.Model):
    comment = models.TextField(default='', blank=True, verbose_name='Коммент')

    class Meta:
        abstract = True
