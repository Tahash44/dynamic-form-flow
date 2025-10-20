from rest_framework import serializers
from .base_field_serializer import BaseFieldSerializer
from ..models import FormTextField

class TextFieldSerializer(BaseFieldSerializer):
    class Meta(BaseFieldSerializer.Meta):
        model = FormTextField
        fields = BaseFieldSerializer.Meta.fields + ['max_length']

    def validate_max_length(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError("max_length must be a positive integer.")
        return value
