from django.contrib import admin
from .models import Form, Field
from ..categories.models import FormCategory


class FieldInline(admin.TabularInline):
    model = Field
    extra = 1
    fields = ('question', 'field_type', 'required', 'position', 'options')
    ordering = ('position',)


@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'is_public', 'created_at')
    list_filter = ('is_public', 'created_at', 'is_deleted')
    search_fields = ('name', 'description')
    inlines = [FieldInline]
    ordering = ('-created_at',)

    def get_queryset(self, request):
        return Form.all_objects.all()


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ('question', 'form', 'field_type', 'required', 'position')
    list_filter = ('field_type', 'required')
    search_fields = ('question',)
    ordering = ('form', 'position')


@admin.register(FormCategory)
class CategoryAdmin(admin.ModelAdmin):
    pass
