from rest_framework import serializers
from rest_framework_serializer_extensions.serializers import SerializerExtensionsMixin

from apps.main.models import (
    Achievement,
    BalanceLog,
    CommandChallenge,
    IndividualChallenge,
    Quest,
    ScoreLog,
)


class QuestSerializer(SerializerExtensionsMixin, serializers.ModelSerializer):
    class Meta:
        model = Quest
        fields = '__all__'


class CompletedQuestSerializer(QuestSerializer):
    completed_at = serializers.DateTimeField(read_only=True)
    coins = serializers.IntegerField()


class AchievementSerializer(SerializerExtensionsMixin, serializers.ModelSerializer):
    assigned_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Achievement
        fields = '__all__'


class AssignedAchievementSerializer(SerializerExtensionsMixin, serializers.ModelSerializer):
    assigned_at = serializers.DateTimeField()

    class Meta:
        model = Achievement
        fields = '__all__'


class BalanceLogSerializer(SerializerExtensionsMixin, serializers.ModelSerializer):
    class Meta:
        model = BalanceLog
        fields = '__all__'


class ScoreLogSerializer(SerializerExtensionsMixin, serializers.ModelSerializer):
    class Meta:
        model = ScoreLog
        fields = '__all__'


class IndividualChallengeSerializer(SerializerExtensionsMixin, serializers.ModelSerializer):
    answer = serializers.CharField(read_only=True)

    class Meta:
        model = IndividualChallenge
        fields = '__all__'
        expandable_fields = {
            'quest': QuestSerializer,
        }


class CommandChallengeSerializer(SerializerExtensionsMixin, serializers.ModelSerializer):
    answer = serializers.CharField(read_only=True)

    class Meta:
        model = CommandChallenge
        fields = '__all__'
        expandable_fields = {
            'quest': QuestSerializer,
        }
