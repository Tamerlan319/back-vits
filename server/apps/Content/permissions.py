from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """
    Разрешает доступ только пользователям с ролью 'admin'
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and request.user.role == 'admin'