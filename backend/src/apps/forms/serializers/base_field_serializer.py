from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from ..models import Field

class BaseFieldSerializer(serializers.ModelSerializer):
    """
    Shared fields + read-only field_type detection.
    """
    field_type = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Field
        fields = [
            'id',
            'form',
            'position',
            'question',
            'description',
            'required',
            'show_position',
            'field_type',  # read-only
        ]
        read_only_fields = ['id', 'field_type']

    def get_field_type(self, obj):
        # e.g. FormTextField -> "text"
        cls_name = obj.__class__.__name__
        # remove prefix 'Form' and suffix 'Field' if exist -> "Text"
        name = cls_name.replace('Form', '').replace('Field', '')
        return name.lower()

    def validate_position(self, value):
        if value is None:
            return value
        if value < 0:
            raise serializers.ValidationError("position cannot be negative.")
        return value

    def run_model_validation(self, instance):
        # helper if you want to call model.clean() before saving
        try:
            instance.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else e.messages)
