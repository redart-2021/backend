import logging
import operator
from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Union,
)

import reversion
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.urls import reverse
from rest_framework import serializers
from reversion.models import Version

from apps.user.models import CustomUser
from apps.user.serializers import UserSerializer

from .models import (
    MailAccount,
    ResponseTemplate,
    Task,
    TaskAdditionField,
    TaskCategory,
    TaskComment,
    TaskFormFieldSettings,
    TaskFormSettings,
    TaskSubcategory,
    Trigger,
)
from .serializers import TaskSerializer

try:
    from utils import mail
except ImportError:
    mail = None

FIELD_TYPE_MAP = {
    serializers.IntegerField: 'int',
    serializers.BooleanField: 'bool',
    serializers.CharField: 'str',
    serializers.URLField: 'url',
    serializers.TimeField: 'time',
    serializers.DateField: 'date',
    serializers.DateTimeField: 'datetime',
    serializers.FloatField: 'float',
    serializers.DecimalField: 'float',
    serializers.PrimaryKeyRelatedField: 'ref',
}

logger = logging.getLogger(__name__)


def get_history(instance: Task) -> List[dict]:
    versions = (Version.objects.get_for_object(instance)
                               .select_related('revision__user')
                               .order_by('revision__date_created'))
    history = []
    for i, version in enumerate(versions[1:]):
        old_version = versions[i]
        history.append({
            'created_at': version.revision.date_created,
            'author': UserSerializer(version.revision.user).data,
            'fields': version_diff(old_version, version),
        })
    return history


def version_diff(old_version: Version, new_version: Version) -> dict:
    old_data, new_data = old_version.field_dict, new_version.field_dict
    keys = set(old_data) | set(new_data)
    if 'updated_at' in keys:
        keys.remove('updated_at')

    diff = {}
    for key in keys:
        old_value, new_value = old_data.get(key), new_data.get(key)
        if old_value != new_value:
            diff[key] = (old_value, new_value)
    return diff


def get_task_schema() -> List[dict]:
    schema = []
    row = 1
    serializer_fields = TaskSerializer().get_fields()
    model_fields = {f.name: f for f in Task._meta.get_fields()}
    for field_name, serializer_field in serializer_fields.items():
        if field_name.endswith('_id'):
            continue

        model_field = model_fields.get(field_name)
        field_schema = {
            'name': serializer_field.label or model_field.verbose_name or field_name,
            'value': field_name,
            'required': serializer_field.required,
            'read_only': serializer_field.read_only,
            'type': FIELD_TYPE_MAP.get(type(serializer_field)),
            'row': row,
            'column': 1,
        }
        if field_schema['type'] == 'ref':
            model_name = model_field.related_model._meta.model_name
            field_schema['method'] = reverse(f'{model_name}-list')
        schema.append(field_schema)
        row += 1
    return schema


def get_task_schema2(category: Optional[TaskCategory] = None,
                     subcategory: Optional[TaskSubcategory] = None) -> List[dict]:
    schema = []
    form = (TaskFormSettings.objects.filter(category=category, subcategory=subcategory)
                                    .prefetch_related('fields')
                                    .first())
    if not form:
        return schema
    form_fields: List[TaskFormFieldSettings] = form.fields.all()
    if not form_fields:
        return schema

    model_fields = {f.name: f for f in Task._meta.get_fields()}
    serializer_fields = TaskSerializer().get_fields()
    additional_fields: Dict[int, TaskAdditionField] = TaskAdditionField.objects.in_bulk()
    for form_field in form_fields:
        model_field = model_fields.get(form_field.field)
        field_schema = {
            'required': form_field.required,
            'row': form_field.row,
            'column': form_field.column,
            'default': form_field.default,
        }
        if model_field:
            serializer_field = serializer_fields[form_field.field]
            field_schema.update({
                'name': serializer_field.label or model_field.verbose_name or form_field.field,
                'value': form_field.field,
                'type': FIELD_TYPE_MAP.get(type(serializer_field)),
            })
            if field_schema['type'] == 'ref':
                model_name = model_field.related_model._meta.model_name
                field_schema['method'] = reverse(f'{model_name}-list')
        else:
            ad_field = additional_fields[int(form_field.field)]
            field_schema.update({
                'name': ad_field.name,
                # тут юзается id доп поля
                'value': TaskAdditionField.name_prefix + form_field.field,
                'type': ad_field.field_type,
            })
            if ad_field.field_type == TaskAdditionField.FieldTypes.CHOICE:
                field_schema['type'] = 'ref'
                field_schema['method'] = reverse(f'{TaskAdditionField._meta.model_name}-choices',
                                                 kwargs={'pk': ad_field.id})
        schema.append(field_schema)

    return schema


def parse_filter(filter_data: dict) -> Q:
    model_fields = {f.name: f for f in Task._meta.get_fields()}
    additional_fields = {TaskAdditionField.name_prefix + str(i)
                         for i in TaskAdditionField.objects.values_list('id', flat=True)}

    exp_map = {
        'and': operator.and_,
        'or': operator.or_,
    }
    op_map = {
        'equal': lambda mf, val: Q(**{mf: val}),
        'not_equal': lambda mf, val: ~Q(**{mf: val}),
        'contains': lambda mf, val: Q(**{mf + '__icontains': val}),
    }
    cond = Q()
    exp = operator.and_

    for line in filter_data:
        if line['name'] in additional_fields:
            # todo: валидация типа
            filtering_name = 'additional_fields__' + line['name']
        elif line['name'] not in model_fields:
            continue
        else:
            model_field = model_fields[line['name']]
            filtering_name = line['name']
            if model_field.many_to_one or model_field.one_to_one:
                rel_model_fields = {f.name for f in model_field.related_model._meta.get_fields()}
                if 'name' not in rel_model_fields:
                    # todo: а то так
                    continue
                filtering_name = line['name'] + '__name'

        field_cond_f = op_map[line['operator']]
        field_cond = field_cond_f(filtering_name, line['value'])
        cond = exp(cond, field_cond)
        exp = exp_map[line['expression']]

    return cond


def mass_edit(tasks: List[Task], fields: List[dict]) -> None:
    # todo: чекнуть тип + доп поля + наличие поля
    # todo: оптимизировать + глубина рекурсии
    model_fields = {f.name: f for f in Task._meta.get_fields()}

    for task in tasks:
        updated_fields = set()
        for pair in fields:
            field = pair['field']
            model_field = model_fields.get(field)
            if model_field and (model_field.many_to_one or model_field.one_to_one):
                field += '_id'
            setattr(task, field, pair['value'])
            if field.startswith(TaskAdditionField.name_prefix):
                updated_fields.add('additional_fields')
            else:
                updated_fields.add(field)
        task.save(update_fields=updated_fields)


def mass_delete(tasks: List[Task]) -> None:
    ids = [t.id for t in tasks]
    Task.objects.filter(id__in=ids).delete()


def merge_tasks(tasks: List[Task], merge_to: Task) -> None:
    ids = [task.id for task in tasks]
    with transaction.atomic():
        TaskComment.objects.filter(task__in=ids).update(task=merge_to)
        Task.objects.filter(id__in=ids).update(duplicate_of=merge_to)
        merge_to.duplicates.extend(ids)
        merge_to.save()


def create_from_comment(comment: TaskComment) -> Task:
    task = comment.task
    new_task = Task.objects.create(
        title=task.title,
        description=comment.text,
        executor=task.executor,
        author=task.author,
        category=task.category,
        project=task.project,
        subcategory=task.subcategory,
        additional_fields=task.additional_fields,
    )
    return new_task


def parse_trigger_conditions(conditions: List[dict]) -> Callable:
    """
    {
        name: task field name
        value: field value to compare
        operator: equal, not_equal, contains, not_contains
        expression: or, and
    }
    """
    # todo: gen class

    def prepare_field_value(instance: Task, field, extra_fields: Optional[dict]) -> str:
        field_name = field if isinstance(field, str) else field.name
        if extra_fields and field_name in extra_fields:
            value = extra_fields[field_name]
        else:
            value = getattr(instance, field_name, None)
        # надеемся на __str__, если fk
        if value is None:
            value = ''
        return str(value).strip().lower()

    def equal(instance: Task, field, expected_value: str, extra_fields) -> bool:
        value = prepare_field_value(instance, field, extra_fields)
        return value == expected_value

    def contains(instance: Task, field, expected_value: str, extra_fields) -> bool:
        value = prepare_field_value(instance, field, extra_fields)
        return expected_value in value

    op_map = {
        'equal': equal,
        'not_equal': lambda *args, **kwargs: not equal(*args, **kwargs),
        'contains': contains,
        'not_contains': lambda *args, **kwargs: not contains(*args, **kwargs),
    }
    exp_map = {
        'and': lambda prev, cur: prev and cur,
        'or': lambda prev, cur: prev or cur,
    }
    model_fields = {f.name: f for f in Task._meta.get_fields()}
    checks = []  # (field, op, exp, value)

    if conditions:
        # из-за начального значения result=True
        conditions[0]['expression'] = 'and'

    for condition in conditions:
        # todo: fk
        exp = exp_map[condition['expression']]
        op = op_map[condition['operator']]
        field = model_fields.get(condition['name'], condition['name'])
        if condition['value'] is None:
            value = ''
        else:
            value = str(condition['value']).strip().lower()
        checks.append((field.name, op, exp, value))

    def evaluate(instance: Task, changed_fields: set, extra_fields: Optional[dict],
                 log_trigger=lambda *args: ...) -> bool:
        result = True
        for i, (field, op, exp, value) in enumerate(checks):
            if field not in changed_fields and field not in extra_fields:
                log_trigger('condition <%s> skip', i)
                return False
            cur = op(instance, field, value, extra_fields)
            log_trigger('condition <%s> result <%s>', i, cur)
            result = exp(result, cur)
        return result

    return evaluate


def parse_trigger_actions(actions: List[dict]) -> Callable:
    """
    {
        name: action name
        args: {
            arg1: val1
            arg2: val2
        }
    }

    prepared action return true, if task has changed
    """
    # todo: gen class

    def change_task(field: str, value) -> Callable:
        # multiple fields?
        model_field = model_fields.get(field)
        if model_field and (model_field.many_to_one or model_field.one_to_one):  # fk
            # todo: user not unique
            field += '_id'
            if not (value is None or isinstance(value, int)):
                value = (model_field.related_model.objects.values_list('id', flat=True)
                                                          .get(name=value))

        def run(instance: Task, _) -> bool:
            if getattr(instance, field, None) != value:
                setattr(instance, field, value)
                return True
            return False

        return run

    def send_notification(template: int, recipients: List[Union[str, int]]) -> Callable:
        template = ResponseTemplate.objects.get(name=template)
        for i, recipient in enumerate(recipients):
            if isinstance(recipient, int):
                recipients[i] = CustomUser.objects.values_list('email', flat=True).get(pk=recipient)

        def run(instance: Task, log_trigger=lambda *args: ...) -> bool:
            body = format_template(template, instance)
            try:
                task_send_notification(instance, body, recipients)
            except Exception:
                logger.exception("can't send notify")
                log_trigger('notify send error')
            return False

        return run

    def get_args(func) -> set:
        code = func.__code__
        return set(code.co_varnames[:code.co_argcount])

    actions_map = {
        'change_task': (change_task, get_args(change_task)),
        'send_notification': (send_notification, get_args(send_notification)),
    }
    model_fields = {f.name: f for f in Task._meta.get_fields()}
    parsed = []

    for raw_action in actions:
        action_creator, required_args = actions_map[raw_action['name']]
        if required_args != set(raw_action['args']):
            raise ValueError

        action = action_creator(**raw_action['args'])
        parsed.append(action)

    def apply(instance: Task, log_trigger=lambda *args: ...) -> None:
        need_save = False
        for action in parsed:
            need_save += action(instance, log_trigger)
        if need_save:
            instance.save()

    return apply


def prepare_trigger(trigger: Trigger) -> Callable:
    conditions = parse_trigger_conditions(trigger.conditions)
    actions = parse_trigger_actions(trigger.actions)

    def run(instance: Task, changed_fields: set, extra_fields: Optional[dict]) -> bool:
        # блок от рекурсии триггеров вида
        #   если поле1 = значение1 то поле2 = значение2
        # вариант 1:
        #   хранение истории
        #   при срабатывании сигнала
        #     заслать чек триггеров в celery
        #     нет ключа - генерить run_id и сохранить в бд и инстанс
        #     повторное сохранение сработает в том же процессе воркера
        #       сигнал прочтет run_id и чекнет состояние оттуда
        #       зашлет чек в celery с указанием стейта

        def log_trigger(msg: str, *args) -> None:
            logging.debug('task <%s>, trigger <%s> ' + msg, instance.id, trigger.name, *args)

        if not hasattr(instance, '_applied_triggers'):
            instance._applied_triggers = set()
        if trigger.id in instance._applied_triggers:
            log_trigger('already applied, skip')
            return False

        if conditions(instance, changed_fields, extra_fields, log_trigger):
            instance._applied_triggers.add(trigger.id)
            with reversion.create_revision():
                reversion.set_comment(f'trigger {trigger.id} - {trigger.name}')
                actions(instance, log_trigger)
            log_trigger('applied')
            return True

        log_trigger('skip')
        return False

    return run


def check_triggers(instance: Task, changed_fields: set, extra_fields: Optional[dict]) -> None:
    triggers = Trigger.objects.filter(enabled=True)  # todo: cache
    for trigger in triggers:
        prepare_trigger(trigger)(instance, changed_fields, extra_fields)


def format_template(template: ResponseTemplate, task: Task) -> str:
    return template.template.format(task=task)


def task_send_notification(instance: Task, body: str,
                           recipients: List[Union[str, CustomUser]]) -> None:
    for i, recipient in enumerate(recipients):
        if recipient == 'author':
            recipients[i] = instance.author.email
        elif recipient == 'executor':
            recipients[i] = instance.executor.email if instance.executor else None
        elif isinstance(recipient, CustomUser):
            recipients[i] = recipient.email
    recipients = [r for r in recipients if r]
    db_acc = MailAccount.objects.filter(project=instance.project_id).first()
    if not db_acc:
        logger.warning('not mail acc for project %s', instance.project_id)
        return

    if mail and settings.EMAIL_ENABLED:
        acc = mail.connect_mail(db_acc.username, db_acc.password, db_acc.smtp_address,
                                db_acc.endpoint)
        mail.send_mail(acc, f'[{instance.id}] {instance.title}', body, recipients)
    else:
        logger.info('mail not enabled or not available')
    logger.info(f'sent {body!r} to {recipients}')
