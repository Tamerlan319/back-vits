import requests
from django.conf import settings

from server.apps.users.models import Group  # Импорт модели группы из другого приложения

class GroupService:
    @staticmethod
    def get_group(group_id):
        try:
            group = Group.objects.get(pk=group_id)
            return {'id': group.id, 'name': group.name}
        except Group.DoesNotExist:
            return None

    @staticmethod
    def validate_group_exists(group_id):
        return Group.objects.filter(pk=group_id).exists()