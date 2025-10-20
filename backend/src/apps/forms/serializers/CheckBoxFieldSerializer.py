from rest_framework import serializers
from .base_field_serializer import BaseFieldSerializer
from ..models import FormCheckBoxField

class CheckBoxFieldSerializer(BaseFieldSerializer):
    class Meta(BaseFieldSerializer.Meta):
        model = FormCheckBoxField
        fields = BaseFieldSerializer.Meta.fields + ['check_box_names', 'minimum', 'maximum']

    def validate_check_box_names(self, value):
        if not isinstance(value, list) or len(value) == 0:
            raise serializers.ValidationError("check_box_names must be a non-empty list of strings.")
        for item in value:
            if not isinstance(item, str):
                raise serializers.ValidationError("All items in check_box_names must be strings.")
        return value

    def validate(self, data):
        minimum = data.get('minimum')
        maximum = data.get('maximum')
        if maximum is not None and minimum is not None and minimum > maximum:
            raise serializers.ValidationError("minimum cannot be greater than maximum.")
        if minimum is not None and minimum < 0:
            raise serializers.ValidationError("minimum must be >= 0.")
        return data
