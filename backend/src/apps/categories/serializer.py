from apps.categories.models import FormCategory,ProcessCategory
from apps.forms.models import Form
from rest_framework import serializers
from apps.processes.models import Process



class FormCategorySerializer(serializers.ModelSerializer):
    forms = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Form.objects.all(),
        required=False
    )

    class Meta:
        model = FormCategory
        fields = ['id', 'name', 'forms']
    def get_forms(self, obj):
        return [
            {
                'id': form.id,
                'name': form.name,
            }
            for form in obj.forms.all()
        ]

class ProcessCategorySerializer(serializers.ModelSerializer):
    process = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Process.objects.all(),
        required=False
    )

    class Meta:
        model = ProcessCategory
        fields = ['id', 'name', 'process']
    def get_process(self, obj):
        return [
            {
                'id': process.id,
                'name': process.name,
            }
            for process in obj.process.all()
        ]

