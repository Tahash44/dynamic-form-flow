from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        process = obj if obj.__class__.__name__ == 'Process' else obj.process
        return getattr(process, 'owner', None) and process.owner.user_id == request.user.id
