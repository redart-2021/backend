# Generated by Django 3.2.7 on 2021-09-04 12:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParsedEventLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата-время создания')),
                ('parsed_data', models.JSONField(default=dict, verbose_name='Обработанные данные')),
                ('locked_by', models.CharField(blank=True, max_length=255, null=True, verbose_name='Кем залочен')),
                ('locked_at', models.DateTimeField(blank=True, null=True, verbose_name='Дата-время лока')),
                ('handled_at', models.DateTimeField(blank=True, null=True, verbose_name='Дата-время выполнения')),
                ('handle_failed', models.BooleanField(default=False, verbose_name='Ошибка выполнения')),
            ],
            options={
                'verbose_name': 'Обработанный входящий лог',
                'verbose_name_plural': 'Обработанные входящие логи',
                'default_related_name': 'parsed_event_logs',
            },
        ),
        migrations.RemoveField(
            model_name='raweventlog',
            name='data',
        ),
        migrations.AddField(
            model_name='raweventlog',
            name='additional_data',
            field=models.JSONField(default=dict, verbose_name='Доп данные'),
        ),
        migrations.AddField(
            model_name='raweventlog',
            name='content_type',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Тип'),
        ),
        migrations.AddField(
            model_name='raweventlog',
            name='parse_failed',
            field=models.BooleanField(default=False, verbose_name='Ошибка разбора'),
        ),
        migrations.AddField(
            model_name='raweventlog',
            name='raw_data',
            field=models.BinaryField(default=b'', verbose_name='Оригинальное сообщение'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='raweventlog',
            name='parsed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата-время разбора'),
        ),
        migrations.DeleteModel(
            name='UserEventLog',
        ),
        migrations.AddField(
            model_name='parsedeventlog',
            name='raw_log',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parsed_event_logs', to='main.raweventlog', verbose_name='Сырой лог'),
        ),
    ]
