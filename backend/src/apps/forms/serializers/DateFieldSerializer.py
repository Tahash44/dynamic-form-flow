# apps/forms/serializers/date_field_serializer.py
from rest_framework import serializers
from .base_field_serializer import BaseFieldSerializer
from ..models import FormDateField

class DateFieldSerializer(BaseFieldSerializer):
    class Meta(BaseFieldSerializer.Meta):
        model = FormDateField
        fields = BaseFieldSerializer.Meta.fields + ['min_date', 'max_date', 'include_time']

    def validate(self, data):
        min_d = data.get('min_date')
        max_d = data.get('max_date')
        if min_d and max_d and min_d > max_d:
            raise serializers.ValidationError("min_date cannot be greater than max_date.")
        return data
