from django.db.models import Max
from rest_framework import serializers
from apps.users.models import Profile
from .models import Process, ProcessStep, ProcessInstance, StepSubmission
from apps.forms.models import Form, Field
from apps.forms.serializer import FormSerializer
from apps.categories.models import ProcessCategory

class StepSubmitPayloadSerializer(serializers.Serializer):
    answers = serializers.DictField(child=serializers.CharField(), required=False)
    password = serializers.CharField(required=False, allow_blank=True)


class StepInlineWriteSerializer(serializers.Serializer):
    form = serializers.PrimaryKeyRelatedField(queryset=Form.objects.all())
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    order = serializers.IntegerField(required=False, min_value=1)


class ProcessStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessStep
        fields = ['id', 'title', 'order', 'form', 'allow_skip']


class ProcessSerializer(serializers.ModelSerializer):
    steps = ProcessStepSerializer(many=True, read_only=True)
    categories = serializers.SerializerMethodField()

    class Meta:
        model = Process
        fields = ['id', 'title', 'type', 'is_active', 'created_at', 'steps', 'categories']
        read_only_fields = ['id', 'created_at']

    def get_categories(self, obj):
        qs = ProcessCategory.objects.filter(process=obj)
        return [{'id': c.id, 'name': c.name} for c in qs]

class ProcessInstanceSerializer(serializers.ModelSerializer):
    started_by = serializers.PrimaryKeyRelatedField(read_only=True)
    process = ProcessSerializer(read_only=True)
    current_step = ProcessStepSerializer(read_only=True)

    class Meta:
        model = ProcessInstance
        fields = [
            'id', 'process', 'started_by', 'status',
            'current_step', 'started_at', 'completed_at'
        ]
        read_only_fields = ['started_by', 'status', 'started_at', 'completed_at']


class StepSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StepSubmission
        fields = ['id', 'instance', 'step', 'form_response', 'submitted_at']
        read_only_fields = ['submitted_at']



class ProcessWriteSerializer(serializers.ModelSerializer):
    steps = StepInlineWriteSerializer(many=True, required=False)
    category_ids = serializers.PrimaryKeyRelatedField(many=True,queryset=ProcessCategory.objects.all(),required=False,write_only=True)

    class Meta:
        model = Process
        fields = ['title', 'type', 'is_active', 'steps', 'category_ids']

    def validate(self, attrs):
        if 'type' not in attrs:
            attrs['type'] = Process.SEQUENTIAL

        ptype = attrs.get('type')
        if ptype not in (Process.SEQUENTIAL, Process.FREE_FLOW):
            raise serializers.ValidationError({'type': 'Invalid process type.'})

        steps_in = self.initial_data.get('steps') or []
        given_orders = [s.get('order') for s in steps_in if s.get('order') is not None]
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
        categories = validated_data.pop('category_ids', [])

        process = Process.objects.create(owner=owner_profile, **validated_data)

        if categories:
            for cat in categories:
                cat.process.add(process)

        next_order = 1
        for item in steps_data:
            form = item['form']
            title = item.get('title', '')
            order = item.get('order') or next_order
            allow_skip = item.get('allow_skip', False)
            ProcessStep.objects.create(process=process,form=form,title=title,order=order,allow_skip=allow_skip)
            next_order = max(next_order + 1, order + 1)

        return process

    def update(self, instance, validated_data):
        categories = validated_data.pop('category_ids', None)
        steps_data = validated_data.pop('steps', None)

        instance.title = validated_data.get('title', instance.title)
        instance.type = validated_data.get('type', instance.type)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()

        if categories is not None:
            old_cats = ProcessCategory.objects.filter(process=instance)
            for c in old_cats:
                c.process.remove(instance)
            for c in categories:
                c.process.add(instance)

        return instance


class ProcessStepWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessStep
        fields = ['title', 'order', 'form', 'allow_skip']

    def _get_process(self):
        return self.context.get('process') or getattr(self.instance, 'process', None)

    def validate(self, attrs):
        process = self._get_process()
        if not process:
            raise serializers.ValidationError({'process': 'Process context is required.'})

        incoming_order = attrs.get('order', getattr(self.instance, 'order', None))

        if process.type == Process.SEQUENTIAL:
            if incoming_order is None:
                raise serializers.ValidationError({'order': 'Order is required for sequential processes.'})
            if incoming_order < 1:
                raise serializers.ValidationError({'order': 'Order must be ≥ 1.'})
        else:
            if incoming_order is not None and incoming_order < 1:
                raise serializers.ValidationError({'order': 'Order must be ≥ 1.'})

        return attrs

    def create(self, validated_data):
        process = self._get_process()
        if process.type == Process.FREE_FLOW and 'order' not in validated_data:
            max_order = process.steps.aggregate(m=Max('order'))['m'] or 0
            validated_data['order'] = max_order + 1

        return ProcessStep.objects.create(process=process, **validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class FreeStepSerializer(serializers.ModelSerializer):
    form = FormSerializer(read_only=True)
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

class FieldReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = [
            'id', 'question', 'field_type', 'required', 'position',
            'options', 'max_length', 'min_value', 'max_value'
        ]

class FormFieldInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = [
            'id',
            'question',
            'field_type',
            'required',
            'position',
            'options',
        ]


class FormInlineSerializer(serializers.ModelSerializer):
    fields = FormFieldInlineSerializer(many=True, read_only=True)

    class Meta:
        model = Form
        fields = [
            'id',
            'name',
            'description',
            'access',
            'slug',
            'fields',
        ]

class CurrentStepSerializer(serializers.ModelSerializer):
    form = FormInlineSerializer(read_only=True)

    class Meta:
        model = ProcessStep
        fields = ['id', 'title', 'order', 'allow_skip', 'form']


class AnswerInputSerializer(serializers.Serializer):
    field_id = serializers.IntegerField()
    value = serializers.CharField(allow_blank=True)

class StepSubmitSimpleSerializer(serializers.Serializer):
    answers = AnswerInputSerializer(many=True)
    password = serializers.CharField(required=False, allow_blank=True, write_only=True)

class StepSubmitJSONSerializer(serializers.Serializer):
    answers = serializers.DictField(
        child=serializers.CharField(allow_blank=True),
        help_text='dict of {field_id: value}'
    )
    password = serializers.CharField(required=False, allow_blank=True)