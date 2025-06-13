from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        print(f"Debug - User: {request.user}")
        print(f"Debug - Role: {getattr(request.user, 'role', None)}")
        print(f"Debug - Is authenticated: {request.user.is_authenticated}")
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and request.user.role == 'admin'