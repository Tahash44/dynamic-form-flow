from rest_framework import serializers
from apps.users.models import Profile
from .models import Process, ProcessStep, ProcessInstance, StepSubmission


class ProcessStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessStep
        fields = ['id', 'title', 'order', 'form']


class ProcessSerializer(serializers.ModelSerializer):
    steps = ProcessStepSerializer(many=True, read_only=True)

    class Meta:
        model = Process
        fields = ['id', 'title', 'type', 'is_active', 'created_at', 'steps']
        read_only_fields = ['id', 'created_at']


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
    class Meta:
        model = StepSubmission
        fields = ['id', 'instance', 'step', 'form_response', 'submitted_at']
        read_only_fields = ['submitted_at']


class ProcessWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Process
        fields = ['title', 'type', 'is_active']

    def validate(self, attrs):
        attrs['type'] = Process.SEQUENTIAL
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            raise serializers.ValidationError({'owner': 'Authentication required to create a process.'})

        owner_profile = getattr(request.user, 'profile', None)
        if owner_profile is None:
            owner_profile = Profile.objects.filter(user=request.user).first()
        if owner_profile is None:
            owner_profile = Profile.objects.create(user=request.user)

        return Process.objects.create(owner=owner_profile, **validated_data)


class ProcessStepWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessStep
        fields = ['title', 'order', 'form']

    def validate(self, attrs):
        process = getattr(self.instance, 'process', None)
        if process and process.type != Process.SEQUENTIAL:
            raise serializers.ValidationError({'process': 'Only sequential processes can have steps here.'})
        return attrs
