from django import forms
from django.contrib import admin
from django.forms.models import BaseInlineFormSet

from .models import Process, ProcessStep, ProcessInstance, StepSubmission


class ProcessStepInlineFormset(BaseInlineFormSet):
    def clean(self):
        super().clean()
        orders = []
        for f in self.forms:
            if f.cleaned_data.get('DELETE', False):
                continue
            if not f.cleaned_data:
                continue
            if f.cleaned_data.get('order'):
                orders.append(f.cleaned_data['order'])
        if len(orders) != len(set(orders)):
            raise forms.ValidationError('Duplicate orders.')


class ProcessStepInline(admin.TabularInline):
    model = ProcessStep
    formset = ProcessStepInlineFormset
    extra = 1
    fields = ['order', 'title', 'form', 'allow_skip']
    autocomplete_fields = ['form']
    ordering = ['order']

@admin.register(ProcessStep)
class ProcessStepAdmin(admin.ModelAdmin):
    list_display = ['id', 'process', 'title', 'order', 'form', 'allow_skip']
    list_filter = ['allow_skip', 'process__type']
    search_fields = ['title', 'process__title', 'form__name']
    autocomplete_fields = ['process', 'form']
    ordering = ['process', 'order']


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'type', 'owner', 'is_active', 'created_at', 'steps_count']
    list_filter = ['type', 'is_active', 'created_at']
    search_fields = ['title', 'owner__user__username']
    date_hierarchy = 'created_at'
    inlines = [ProcessStepInline]

    def steps_count(self, obj):
        return obj.steps.count()
    steps_count.short_description = 'Step count'


@admin.register(ProcessInstance)
class ProcessInstanceAdmin(admin.ModelAdmin):
    list_display = ['id', 'process', 'started_by', 'status', 'current_step', 'started_at', 'completed_at']
    list_filter = ['status', 'started_at', 'completed_at', 'process__type']
    search_fields = ['process__title', 'started_by__username', 'access_token']
    readonly_fields = ['started_at', 'completed_at', 'access_token', 'access_token_expires_at']
    autocomplete_fields = ['process', 'started_by', 'current_step']