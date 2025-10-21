from rest_framework import serializers
from .base_field_serializer import BaseFieldSerializer
from ..models import FormSelectField

class SelectFieldSerializer(BaseFieldSerializer):
    class Meta(BaseFieldSerializer.Meta):
        model = FormSelectField
        fields = BaseFieldSerializer.Meta.fields + ['options']

    def validate_options(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("options must be a list.")
        if len(value) == 0:
            raise serializers.ValidationError("options cannot be empty.")
        for opt in value:
            if not isinstance(opt, str):
                raise serializers.ValidationError("each option must be a string (or use dict label/value if you change format).")
        return value
