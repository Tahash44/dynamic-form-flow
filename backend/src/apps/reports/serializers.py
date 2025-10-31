from rest_framework import serializers
from apps.forms.models import Form, Response, Answer
from django.db.models import Avg, Min, Max, Count

class FormReportSerializer(serializers.ModelSerializer):
    report = serializers.SerializerMethodField()

    class Meta:
        model = Form
        fields = ['id', 'name', 'report']

    def get_report(self, obj):
        report = []
        for field in obj.fields.all():
            answers = Answer.objects.filter(field=field)
            stats = {}

            if field.field_type == 'number':
                stats = answers.aggregate(
                    average=Avg('value'),
                    min=Min('value'),
                    max=Max('value'),
                    count=Count('id')
                )

            elif field.field_type in ['select', 'checkbox']:
                options_count = {}
                for a in answers:
                    if field.field_type == 'checkbox':
                        selected = a.value.split(',')  
                        for s in selected:
                            s = s.strip()
                            options_count[s] = options_count.get(s, 0) + 1
                    else:
                        options_count[a.value] = options_count.get(a.value, 0) + 1
                stats = options_count

            if stats:
                report.append({
                    'question': field.question,
                    'type': field.field_type,
                    'stats': stats
                })

        return report


class FormStatsSerializer(serializers.ModelSerializer):
    responses_count = serializers.SerializerMethodField()

    class Meta:
        model = Form
        fields = ['id', 'name', 'views_count', 'responses_count', 'created_at']

    def get_responses_count(self, obj):
        return Response.objects.filter(form=obj).count()


class AnswerReportSerializer(serializers.ModelSerializer):
    question = serializers.CharField(source='field.question', read_only=True)

    class Meta:
        model = Answer
        fields = ['question', 'value']


class ResponseReportSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', default=None)
    answers = AnswerReportSerializer(many=True, read_only=True)

    class Meta:
        model = Response
        fields = ['id', 'user', 'submitted_at', 'answers']


class FormResponsesReportSerializer(serializers.ModelSerializer):
    responses = ResponseReportSerializer(many=True, read_only=True)

    class Meta:
        model = Form
        fields = ['id', 'name', 'responses']
