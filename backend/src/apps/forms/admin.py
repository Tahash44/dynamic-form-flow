from django.contrib import admin
from .models import Form, Field, Response, Answer


class FieldInline(admin.TabularInline):
    model = Field
    extra = 1
    fields = ('question', 'field_type', 'required', 'position', 'options')
    ordering = ('position',)


@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'access', 'created_by', 'created_at', 'slug']
    list_filter = ('access', 'created_at')
    search_fields = ['name', 'description', 'slug', 'created_by__username']
    inlines = [FieldInline]
    ordering = ('-created_at',)


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ('question', 'form', 'field_type', 'required', 'position')
    list_filter = ('field_type', 'required')
    search_fields = ('question',)
    ordering = ('form', 'position')

@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('id', 'form', 'user', 'submitted_at')
    list_filter = ('user', 'submitted_at')
    readonly_fields = ('submitted_at',)
    ordering = ('-submitted_at',)

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'response', 'field', 'value')
    list_filter = ('response',)
    readonly_fields = ('value',)