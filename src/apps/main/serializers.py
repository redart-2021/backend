from rest_framework import serializers
from rest_framework_serializer_extensions.serializers import SerializerExtensionsMixin

from drf_spectacular.utils import extend_schema_field, OpenApiTypes

from apps.main.models import (
    Quest,
)
from apps.user.serializers import UserSerializer


@extend_schema_field(OpenApiTypes.ANY)
class AnyField(serializers.Field):
    def to_internal_value(self, value: any) -> any:
        return value

    def to_representation(self, value: any) -> any:
        return value


class QuestSerializer(SerializerExtensionsMixin, serializers.ModelSerializer):
    class Meta:
        model = Quest
        fields = '__all__'
