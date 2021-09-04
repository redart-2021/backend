from django.db.models import F, Subquery, OuterRef
from django_filters import rest_framework as filters
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_serializer_extensions.views import SerializerExtensionsAPIViewMixin

from .models import (
    Achievement,
    BalanceLog,
    CommandChallenge,
    IndividualChallenge,
    Quest,
    RawEventLog,
    ScoreLog,
    UserAchievement,
)
from .serializers import (
    AchievementSerializer,
    BalanceLogSerializer,
    CommandChallengeSerializer,
    CompletedQuestSerializer,
    IndividualChallengeSerializer,
    QuestSerializer,
    ScoreLogSerializer,
)
from .tasks import (
    parse_event,
)


class IngestLogView(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, format=None) -> Response:
        data = request.stream.read()
        event = RawEventLog.objects.create(
            raw_data=data,
            content_type=request.content_type,
        )
        parse_event(event)
        return Response(status=201)


class QuestViewSet(SerializerExtensionsAPIViewMixin,
                   viewsets.GenericViewSet,
                   mixins.ListModelMixin,
                   mixins.RetrieveModelMixin):
    model = Quest
    queryset = model.objects.all()
    serializer_class = QuestSerializer
    search_fields = ('name',)

    def get_serializer_class(self):
        if self.action == 'completed':
            return CompletedQuestSerializer
        return QuestSerializer

    @action(methods=['GET'], detail=False)
    def completed(self, request):
        blt = 'main_balancelog'
        ubt = 'main_userbalance'
        qs = Quest.objects.extra(  # noqa: S610
            tables=[blt, ubt],
            where=[
                f"main_quest.id = ({blt}.additional_data->>'quest')::int",
                f'{blt}.balance_id = {ubt}.balance_id',
                f'{ubt}.user_id = {request.user.id}',
            ],
            select={
                'completed_at': f'{blt}.created_at',
                'coins': f'{blt}.amount',
            }
        ).order_by('-completed_at')
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class AchievementViewSet(SerializerExtensionsAPIViewMixin,
                         viewsets.GenericViewSet,
                         mixins.ListModelMixin,
                         mixins.RetrieveModelMixin):
    model = Achievement
    queryset = model.objects.all()
    serializer_class = AchievementSerializer

    def get_queryset(self):
        return self.queryset.annotate(
            assigned_at=Subquery(UserAchievement.objects.filter(
                achievement=OuterRef('id'),
                user=self.request.user
            ).values('created_at')[:1]),
        )


class BalanceViewSet(SerializerExtensionsAPIViewMixin,
                     viewsets.GenericViewSet,
                     mixins.RetrieveModelMixin,
                     mixins.ListModelMixin):
    model = BalanceLog
    queryset = BalanceLog.objects.order_by('-created_at')
    serializer_class = BalanceLogSerializer

    def get_queryset(self):
        return self.queryset.filter(balance__user_balance__user=self.request.user)


class ScoreViewSet(SerializerExtensionsAPIViewMixin,
                   viewsets.GenericViewSet,
                   mixins.ListModelMixin,
                   mixins.RetrieveModelMixin):
    model = ScoreLog
    queryset = model.objects.order_by('-created_at')
    serializer_class = ScoreLogSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class ChallengeFilterSet(filters.FilterSet):
    answer = filters.CharFilter()


class IndividualChallengesViewSet(SerializerExtensionsAPIViewMixin,
                                  viewsets.GenericViewSet,
                                  mixins.RetrieveModelMixin,
                                  mixins.ListModelMixin,
                                  mixins.CreateModelMixin):
    model = IndividualChallenge
    queryset = model.objects.annotate(answer=F('requests__answer')).order_by('-id')
    serializer_class = IndividualChallengeSerializer
    filterset_class = ChallengeFilterSet
    extensions_expand = {'quest'}

    def get_queryset(self):
        return self.queryset.filter(requests__member=self.request.user)


class CommandChallengesViewSet(SerializerExtensionsAPIViewMixin,
                               viewsets.GenericViewSet,
                               mixins.RetrieveModelMixin,
                               mixins.ListModelMixin,
                               mixins.CreateModelMixin):
    model = CommandChallenge
    queryset = model.objects.annotate(answer=F('requests__answer')).order_by('-id')
    serializer_class = CommandChallengeSerializer
    filterset_class = ChallengeFilterSet
    extensions_expand = {'quest'}

    def get_queryset(self):
        return self.queryset.filter(requests__member__users=self.request.user)
