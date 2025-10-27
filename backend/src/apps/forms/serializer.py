from rest_framework import serializers
from .models import Form, Field, Answer, Response


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