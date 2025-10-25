from apps.categories.models import FormCategory
from apps.forms.models import Form
from rest_framework import serializers


class CategorySerializer(serializers.ModelSerializer):
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
