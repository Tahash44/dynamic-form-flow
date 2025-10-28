from django.contrib import admin
from .models import Form, Field


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
