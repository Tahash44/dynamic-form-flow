from rest_framework import serializers
from apps.users.models import Profile
from .models import Process, ProcessStep, ProcessInstance, StepSubmission
from apps.forms.models import Form


class StepInlineWriteSerializer(serializers.Serializer):
    form = serializers.PrimaryKeyRelatedField(queryset=Form.objects.all())
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    order = serializers.IntegerField(required=False, min_value=1)


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
    steps = StepInlineWriteSerializer(many=True, required=False)

    class Meta:
        model = Process
        fields = ['title', 'type', 'is_active', 'steps']

    def validate(self, attrs):
        ptype = attrs.get('type')
        if ptype not in (Process.SEQUENTIAL, Process.FREE_FLOW):
            raise serializers.ValidationError({'type': 'Invalid process type.'})

        steps = self.initial_data.get('steps') or []
        given_orders = [s.get('order') for s in steps if s.get('order') is not None]
        if len(given_orders) != len(set(given_orders)):
            raise serializers.ValidationError({'steps': 'Duplicate orders are not allowed.'})


        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            raise serializers.ValidationError({'owner': 'Authentication required to create a process.'})

        owner_profile = getattr(request.user, 'profile', None) \
            or Profile.objects.filter(user=request.user).first() \
            or Profile.objects.create(user=request.user)

        steps_data = validated_data.pop('steps', [])
        process = Process.objects.create(owner=owner_profile, **validated_data)

        next_order = 1
        for item in steps_data:
            form = item['form']
            title = item.get('title', '')
            order = item.get('order') or next_order
            ProcessStep.objects.create(process=process, form=form, title=title, order=order)
            next_order = max(next_order + 1, order + 1)

        return process

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
