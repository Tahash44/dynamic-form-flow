from rest_framework import serializers
from .models import Form, Field


class FieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = '__all__'


class FormSerializer(serializers.ModelSerializer):
    fields = FieldSerializer(many=True, read_only=True)
    categories = serializers.SerializerMethodField()

    class Meta:
        model = Form
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at')

    def get_categories(self, obj):
        return [
            {
                'id': category.id,
                'name': category.name
            }
            for category in obj.categories.all()
        ]

