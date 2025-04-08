from rest_framework import permissions

class EventPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.role == 'guest':
            return request.method in permissions.SAFE_METHODS  # Только чтение
        
        if request.method == 'POST':
            return request.user.role in ['student', 'teacher', 'admin']
        
        return True

    def has_object_permission(self, request, view, obj):
        # Личные события видны только создателю
        if obj.event_type == 'personal':
            return obj.creator == request.user
        
        # Гости могут видеть только общие события
        if request.user.role == 'guest':
            return obj.event_type == 'global'
        
        # Студенты могут видеть только свои групповые события
        if request.user.role == 'student':
            if obj.event_type == 'group':
                return obj.group_id in request.user.student_groups.values_list('id', flat=True)
            return True
        
        return True