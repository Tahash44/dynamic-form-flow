from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models import Field
from ..serializers.base_field_serializer import BaseFieldSerializer
from ..serializers.dynamic_field_serializer import DynamicFieldSerializer
from ..serializers.field_factory import get_serializer_class_by_type
from rest_framework.permissions import AllowAny

class FieldViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    # ViewSet for handling field objects (update/delete phase)

    queryset = Field.objects.all()
    lookup_field = 'id'

    def get_serializer_class(self):
        """
        Use dynamic serializer for create/update,and base serializer for read operations.
        """
        if self.action in ['create', 'update', 'partial_update']:
            return DynamicFieldSerializer
        return BaseFieldSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(BaseFieldSerializer(instance).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance=instance,
            data=request.data,
            partial=kwargs.get('partial', False),
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        field_type = instance.__class__.__name__.replace('Form', '').replace('Field', '').lower()
        concrete_serializer = get_serializer_class_by_type(field_type)(
            instance, context={'request': request}
        )
        return Response(concrete_serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
