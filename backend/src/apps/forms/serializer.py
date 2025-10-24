from rest_framework import serializers
from .models import Form, Field, Category


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


class CategorySerializer(serializers.ModelSerializer):
    forms = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'forms']

    def get_forms(self, obj):
        return [
            {
                'id': form.id,
                'name': form.name,
            }
            for form in obj.forms.all()
        ]
