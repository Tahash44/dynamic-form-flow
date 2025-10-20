from rest_framework import serializers
from .field_factory import get_serializer_class_by_type

class DynamicFieldSerializer(serializers.Serializer):

    field_type = serializers.ChoiceField(choices=list(get_serializer_class_by_type.__defaults__[0].keys()) if False else ['text','select','checkbox','number','date'])

    def to_internal_value(self, data):
        field_type = data.get('field_type')
        if not field_type:
            raise serializers.ValidationError({'field_type': 'This field is required.'})
        serializer_class = get_serializer_class_by_type(field_type)
        serializer = serializer_class(data=data, context=self.context)
        serializer.is_valid(raise_exception=True)
        self._concrete_serializer = serializer
        return serializer.validated_data

    def create(self, validated_data):
        return self._concrete_serializer.save()

    def update(self, instance, validated_data):
        serializer_class = validated_data.pop('_concrete_serializer')
        serializer = serializer_class(instance=instance, data=validated_data, partial=self.partial, context=self.context)
        serializer.is_valid(raise_exception=True)
        return serializer.save()
