from django.conf.urls import url
from django.urls import include
from django.views.generic import TemplateView, RedirectView
from rest_framework.routers import DefaultRouter

from .views import (
    AchievementViewSet,
    BalanceViewSet,
    CommandChallengesViewSet,
    IndividualChallengesViewSet,
    IngestLogView,
    QuestViewSet,
    ScoreViewSet,
)

router = DefaultRouter()
router.register('quests', QuestViewSet)
router.register('achievements', AchievementViewSet)
router.register('balance', BalanceViewSet)
router.register('score', ScoreViewSet)
router.register('challenges/individual', IndividualChallengesViewSet)
router.register('challenges/command', CommandChallengesViewSet)

urlpatterns = [
    url(r'^api/v1/', include(router.urls)),
    url(r'^api/v1/log', IngestLogView.as_view()),
    url(r'^$', TemplateView.as_view(template_name='main/index.html')),
    url(r'^home', RedirectView.as_view(url='/')),
    url(r'^login', RedirectView.as_view(url='/')),
    url(r'^static/main', RedirectView.as_view(url='/')),
]
