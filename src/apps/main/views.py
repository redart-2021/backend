from django.db.models import (
    F,
    Func,
    Q,
)
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import mixins, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_serializer_extensions.views import SerializerExtensionsAPIViewMixin
from reversion.views import RevisionMixin

from apps.main.models import (
)
from apps.main.serializers import (
)
from apps.main.services import (
)


class SomeViewSet(ModelViewSet):
    model = ...
    queryset = model.objects.all()
    serializer_class = ...
    search_fields = ('name',)
    filterset_fields = ('category',)


class SomeFilterSet(filters.FilterSet):
    filter = filters.NumberFilter(method='apply_filter')  # noqa: A003, VNE003
    id = filters.NumberFilter(method='filter_by_id')  # noqa: A003, VNE003
    duplicates = filters.BooleanFilter(method='filter_duplicates')

    class Meta:
        model = ...
        fields = ('status', 'project', 'category', 'subcategory', 'author', 'executor',
                  'duplicate_of')


class TaskViewSet(SerializerExtensionsAPIViewMixin, RevisionMixin, ModelViewSet):
    model = Task
    queryset = model.objects.select_related('status', 'project', 'category', 'subcategory',
                                            'author', 'executor').filter(duplicate_of=None)
    serializer_class = TaskSerializer
    filterset_class = TaskFilterSet
    extensions_expand = {'status', 'project', 'category', 'subcategory', 'author', 'executor'}
    search_fields = ('title',
                     'status__name', 'project__name', 'category__name', 'subcategory__name',
                     'author__first_name', 'author__last_name', 'author__middle_name',
                     'executor__first_name', 'executor__last_name', 'executor__middle_name')

    def get_serializer_context(self) -> dict:  # todo: дичь 2
        context = super().get_serializer_context()
        if self.action in ('create', 'update', 'partial_update'):
            context.pop('expand', None)
            exp = {f + '_id' for f in self.extensions_expand} | {'author'}
            context.setdefault('exclude', set()).update(exp)
        return context

    def get_queryset(self):
        return self.queryset.filter(executor=self.request.user)

    def create(self, request, *args, **kwargs) -> Response:  # todo: дичь 3
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=self.request.user)
        context = super().get_serializer_context()
        serializer_out = self.get_serializer(serializer.instance, context=context)
        return Response(serializer_out.data, status=201)

    def update(self, request, pk: int, partial: bool) -> Response:  # todo: дичь 4
        instance = self.get_object()
        serializer = self.get_serializer(instance, partial=partial, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        context = super().get_serializer_context()
        serializer_out = self.get_serializer(instance, context=context)
        return Response(serializer_out.data, status=200)

    @extend_schema(
        responses={200: {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'value': {},
                },
                'required': ['name', 'value'],
            },
        }},
    )
    @action(methods=['GET'], detail=False)
    def available_filters(self, request) -> Response:
        filters = defaultdict(list)
        fields = self.filterset_class.get_fields().keys()
        qs = self.get_queryset()
        for field in fields:
            model_field = self.model._meta.get_field(field)
            name_field = field
            if model_field.is_relation:
                rel_fields = {f.name: f for f in model_field.related_model._meta.fields}
                if 'name' in rel_fields:
                    name_field = f'{field}__name'
            values = list(qs.annotate(name=F(name_field), value=F(field))
                            .values('name', 'value')
                            .exclude(value=None)
                            .distinct())
            if values:
                filters[field] = values
        additional = (qs.annotate(key=Func('additional_fields', function='jsonb_object_keys'),
                                  value=Func('additional_fields', 'key',
                                             function='jsonb_extract_path'))
                        .values_list('key', 'value')
                        .distinct())
        for field, value in additional:
            filters[field].append({'name': value, 'value': value})
        return Response(filters)

    @action(methods=['GET'], url_path='schema', detail=False)
    def _schema(self, request) -> Response:
        schema = get_task_schema()
        return Response(schema)

    @action(methods=['GET'], detail=False)
    def schema2(self, request) -> Response:
        serializer = GetSchemaSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        schema = get_task_schema2(data.get('category'), data.get('subcategory'))
        return Response(schema)

    @extend_schema(
        request=MassEditSerializer,
        responses={204: None},
    )
    @action(methods=['POST'], detail=False)
    def mass_edit(self, request) -> Response:
        serializer = MassEditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        mass_edit(data['tasks'], data['fields'])
        return Response(status=204)

    @extend_schema(
        request=MassDeleteSerializer,
        responses={204: None},
    )
    @action(methods=['POST'], detail=False)
    def mass_delete(self, request) -> Response:
        serializer = MassDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        mass_delete(data['tasks'])
        return Response(status=204)

    @extend_schema(
        request=MergeTasksSerializer,
        responses={204: None},
    )
    @action(methods=['POST'], detail=False)
    def merge(self, request) -> Response:
        serializer = MergeTasksSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        merge_tasks(data['tasks'], data['merge_to'])
        return Response(status=204)

    @extend_schema(
        request=CreateFromCommentSerializer,
        responses={201: TaskSerializer},
    )
    @action(methods=['POST'], detail=False)
    def from_comment(self, request) -> Response:
        serializer = CreateFromCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        task = create_from_comment(data['comment'])
        serializer = self.get_serializer(task)
        return Response(serializer.data, status=201)

    @extend_schema(
        responses={200: {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'created_at': {
                        'type': 'string',
                        'format': 'date-time',
                    },
                    'author': {},
                    'fields': {
                        'type': 'array',
                        'items': {
                            'type': 'array',
                            'items': {},
                            'minItems': 2,
                            'maxItems': 2,
                        }
                    },
                },
                'required': ['created_at', 'author', 'fields'],
            },
        }},
    )
    @action(methods=['GET'], detail=True)
    def history(self, request, pk) -> Response:
        task = self.get_object()
        history = get_history(task)
        return Response(history)


class TaskCommentViewSet(SerializerExtensionsAPIViewMixin,
                         viewsets.GenericViewSet,
                         mixins.CreateModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.ListModelMixin):
    model = TaskComment
    queryset = model.objects.all()
    serializer_class = TaskCommentSerializer
    filterset_fields = ('task', 'author')
    search_fields = ('text',)
    extensions_expand = {'author'}

    def get_serializer_context(self) -> dict:  # todo: и снова дичь
        context = super().get_serializer_context()
        if self.action in ('create', 'update', 'partial_update'):
            context.pop('expand', None)
            exp = {f + '_id' for f in self.extensions_expand}
            context.setdefault('exclude', set()).update(exp)
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        context = super().get_serializer_context()
        serializer_out = self.get_serializer(serializer.instance, context=context)
        return Response(serializer_out.data, status=201)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        task = serializer.instance.task
        if task.author_id != self.request.user.id:
            task_send_notification(task, serializer.instance.text, ['author'])


class AdditionFieldsViewSet(ModelViewSet):
    model = TaskAdditionField
    queryset = model.objects.all()
    serializer_class = TaskAdditionFieldSerializer
    search_fields = ('name',)

    @extend_schema(
        responses={200: {
            'type': 'object',
            'properties': {
                'results': {
                    'type': 'array',
                    'items': {},
                },
            },
        }},
    )
    @action(methods=['GET'], detail=True)
    def choices(self, request, pk: int) -> Response:
        field: AdditionFieldsViewSet.model = self.get_object()
        data = {'results': field.choices}
        return Response(data)


class ResponseTemplateViewSet(ModelViewSet):
    model = ResponseTemplate
    queryset = model.objects.all()
    serializer_class = ResponseTemplateSerializer
    search_fields = ('name',)


class SavedTaskFilterViewSet(ModelViewSet):
    model = SavedTaskFilter
    queryset = model.objects.all()
    serializer_class = SavedTaskFilterSerializer
    search_fields = ('name',)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TriggerViewSet(ModelViewSet):
    model = Trigger
    queryset = model.objects.all()
    serializer_class = TriggerSerializer
    search_fields = ('name',)
