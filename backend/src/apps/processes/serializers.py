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
        attrs['type'] = attrs.get('type', Process.SEQUENTIAL)
        if attrs['type'] not in dict(Process.TYPE_CHOICES):
            raise serializers.ValidationError({'type': 'Invalid process type.'})
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
        process = getattr(self.instance, 'process', None) or self.context.get('process')
        if process and process.type != Process.SEQUENTIAL:
            raise serializers.ValidationError({'process': 'Only sequential processes can have steps here.'})
        return attrs


class FreeStepSerializer(serializers.ModelSerializer):
    is_submitted = serializers.SerializerMethodField()

    class Meta:
        model = ProcessStep
        fields = ['id', 'title', 'order', 'form', 'is_submitted']

    def get_is_submitted(self, obj):
        submitted = self.context.get('submitted_step_ids')
        if isinstance(submitted, set):
            return obj.id in submitted
        instance = self.context.get('instance')
        if not instance:
            return False
        return StepSubmission.objects.filter(instance=instance, step=obj).exists()

# #freeflow
#
# class FreeFlowProcessSerializer(ProcessSerializer):
#     class Meta(ProcessSerializer.Meta):
#         model = Process
#         fields = ['id', 'title', 'type', 'access', 'is_active', 'steps']
#
# class FreeFlowProcessWriteSerializer(ProcessWriteSerializer):
#     class Meta(ProcessWriteSerializer.Meta):
#         model = Process
#         fields = ['id', 'title', 'type', 'access', 'password', 'is_active']
#         extra_kwargs = ProcessWriteSerializer.Meta.extra_kwargs
#
#     def validate(self, attrs):
#         attrs['type'] = Process.FREE_FLOW
#         if attrs.get('access') == getattr(Process, 'PRIVATE', None) and not (attrs.get('password') or '').strip():
#             raise serializers.ValidationError({'password': 'Password is required for private processes.'})
#         return attrs
#
#     def create(self, validated_data):
#         request = self.context['request']
#         owner = getattr(request.user, 'profile', None)
#         if not owner:
#             raise serializers.ValidationError({'owner': 'Profile not found for user.'})
#         return Process.objects.create(owner=owner, **validated_data)
#
# class FreeFlowStepWriteSerializer(ProcessStepWriteSerializer):
#     class Meta(ProcessStepWriteSerializer.Meta):
#         model = ProcessStep
#         fields = ['id', 'title', 'order', 'form', 'process']
#
#     def validate(self, attrs):
#         process = attrs.get('process') or getattr(self.instance, 'process', None)
#         if process and process.type != Process.FREE_FLOW:
#             raise serializers.ValidationError({'process': 'This serializer is for free-flow processes only.'})
#         return attrs
#
#
# #freeflow
#
# class FreeFlowProcessSerializer(ProcessSerializer):
#     class Meta(ProcessSerializer.Meta):
#         model = Process
#         fields = ['id', 'title', 'type', 'access', 'is_active', 'steps']
#
# class FreeFlowProcessWriteSerializer(ProcessWriteSerializer):
#     class Meta(ProcessWriteSerializer.Meta):
#         model = Process
#         fields = ['id', 'title', 'type', 'access', 'password', 'is_active']
#         extra_kwargs = ProcessWriteSerializer.Meta.extra_kwargs
#
#     def validate(self, attrs):
#         attrs['type'] = Process.FREE_FLOW
#         if attrs.get('access') == getattr(Process, 'PRIVATE', None) and not (attrs.get('password') or '').strip():
#             raise serializers.ValidationError({'password': 'Password is required for private processes.'})
#         return attrs
#
#     def create(self, validated_data):
#         request = self.context['request']
#         owner = getattr(request.user, 'profile', None)
#         if not owner:
#             raise serializers.ValidationError({'owner': 'Profile not found for user.'})
#         return Process.objects.create(owner=owner, **validated_data)
#
# class FreeFlowStepWriteSerializer(ProcessStepWriteSerializer):
#     class Meta(ProcessStepWriteSerializer.Meta):
#         model = ProcessStep
#         fields = ['id', 'title', 'order', 'form', 'process']
#
#     def validate(self, attrs):
#         process = attrs.get('process') or getattr(self.instance, 'process', None)
#         if process and process.type != Process.FREE_FLOW:
#             raise serializers.ValidationError({'process': 'This serializer is for free-flow processes only.'})
#         return attrs
