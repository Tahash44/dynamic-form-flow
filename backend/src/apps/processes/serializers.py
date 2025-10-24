from rest_framework import serializers
from .models import Process, ProcessStep, ProcessInstance, StepSubmission


class ProcessStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessStep
        fields = ['id', 'title', 'order', 'form']


class ProcessSerializer(serializers.ModelSerializer):
    steps = ProcessStepSerializer(many=True, read_only=True)

    class Meta:
        model = Process
        fields = ['id', 'title', 'type', 'access', 'is_active', 'steps']


class ProcessInstanceSerializer(serializers.ModelSerializer):
    process = ProcessSerializer(read_only=True)
    current_step = ProcessStepSerializer(read_only=True)

    class Meta:
        model = ProcessInstance
        fields = [
            'id', 'process', 'started_by', 'status',
            'current_step', 'started_at', 'completed_at'
        ]
        read_only_fields = ['status', 'started_at', 'completed_at']


class StepSubmissionSerializer(serializers.ModelSerializer):
    step = ProcessStepSerializer(read_only=True)

    class Meta:
        model = StepSubmission
        fields = ['id', 'instance', 'step', 'form_response', 'submitted_at']
        read_only_fields = ['submitted_at']


class ProcessWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Process
        fields = ['id', 'title', 'type', 'access', 'password', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
        }

    def validate(self, attrs):
        attrs['type'] = Process.SEQUENTIAL
        if attrs.get('access') == Process.PRIVATE and not (attrs.get('password') or '').strip():
            raise serializers.ValidationError({'password': 'Password is required for private processes.'})
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        owner = getattr(request.user, 'profile', None)
        if not owner:
            raise serializers.ValidationError({'owner': 'Profile not found for user.'})
        return Process.objects.create(owner=owner, **validated_data)


class ProcessStepWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessStep
        fields = ['id', 'title', 'order', 'form', 'process']

    def validate(self, attrs):
        process = attrs.get('process') or getattr(self.instance, 'process', None)
        if process and process.type != Process.SEQUENTIAL:
            raise serializers.ValidationError({'process': 'Only sequential processes can have steps here.'})
        return attrs
