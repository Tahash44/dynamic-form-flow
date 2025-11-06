from rest_framework import serializers
from .models import Form, Field, Answer, Response
from ..categories.models import FormCategory


class FieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = '__all__'


class FormSerializer(serializers.ModelSerializer):
    fields = FieldSerializer(many=True, read_only=True)
    categories = serializers.SerializerMethodField()
    category_ids = serializers.PrimaryKeyRelatedField(
        source='categories',
        many=True,
        queryset=FormCategory.objects.all(),
        write_only=True,
        required=False
    )

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

    def create(self, validated_data):
        categories = validated_data.pop('categories', [])
        form = super().create(validated_data)
        if categories:
            form.categories.set(categories)
        return form

    def update(self, instance, validated_data):
        categories = validated_data.pop('categories', None)
        form = super().update(instance, validated_data)
        if categories is not None:
            form.categories.set(categories)
        return form


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'field', 'value']

class ResponseSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)

    class Meta:
        model = Response
        fields = ['id', 'form', 'user', 'submitted_at', 'answers']
        read_only_fields = ['user', 'submitted_at']

    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        response = Response.objects.create(**validated_data)
        for answer_data in answers_data:
            Answer.objects.create(response=response, **answer_data)
        return response
