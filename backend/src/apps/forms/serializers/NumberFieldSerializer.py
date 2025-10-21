from rest_framework import serializers
from .base_field_serializer import BaseFieldSerializer
from ..models import FormNumberField

class NumberFieldSerializer(BaseFieldSerializer):
    class Meta(BaseFieldSerializer.Meta):
        model = FormNumberField
        fields = BaseFieldSerializer.Meta.fields + ['min_value', 'max_value', 'decimal_allowed']

    def validate(self, data):
        minv = data.get('min_value')
        maxv = data.get('max_value')
        if minv is not None and maxv is not None and minv > maxv:
            raise serializers.ValidationError("min_value cannot be greater than max_value.")
        return data
