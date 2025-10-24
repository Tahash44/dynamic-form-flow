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
