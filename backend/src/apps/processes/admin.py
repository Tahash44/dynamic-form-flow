from django.contrib import admin
from .models import Process, ProcessStep, ProcessInstance, StepSubmission


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner', 'type', 'is_active', 'created_at')
    list_filter = ('type', 'is_active')
    search_fields = ('title', 'owner__user__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('title', 'owner', 'type', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
        }),
    )


@admin.register(ProcessStep)
class ProcessStepAdmin(admin.ModelAdmin):
    list_display = ('id', 'process', 'title', 'form', 'order')
    list_filter = ('process',)
    search_fields = ('title', 'process__title', 'form__name')
    ordering = ('process', 'order')
    list_editable = ('order',)


@admin.register(ProcessInstance)
class ProcessInstanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'process', 'started_by', 'status', 'current_step', 'started_at', 'completed_at')
    list_filter = ('status', 'process')
    search_fields = ('process__title', 'started_by__username')
    ordering = ('-started_at',)
    readonly_fields = ('started_at', 'completed_at')


@admin.register(StepSubmission)
class StepSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'instance', 'step', 'submitted_at')
    list_filter = ('step__process',)
    search_fields = ('instance__process__title', 'step__title')
    ordering = ('-submitted_at',)
    readonly_fields = ('submitted_at',)
