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

    @staticmethod
    def get_group(group_id):
        """Получает информацию о группе из сервиса групп"""
        try:
            response = requests.get(
                f"{settings.GROUP_SERVICE_URL}/api/groups/{group_id}/",
                headers={'Authorization': f'Bearer {settings.GROUP_SERVICE_TOKEN}'}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None

    @staticmethod
    def get_group_members(group_id, role=None):
        """Получает список участников группы"""
        try:
            url = f"{settings.GROUP_SERVICE_URL}/api/groups/{group_id}/members/"
            if role:
                url += f"?role={role}"
                
            response = requests.get(
                url,
                headers={'Authorization': f'Bearer {settings.GROUP_SERVICE_TOKEN}'}
            )
            response.raise_for_status()
            return [member['id'] for member in response.json()]
        except requests.RequestException:
            return []

    @staticmethod
    def get_user_groups(user_id):
        """Получает список групп пользователя"""
        try:
            response = requests.get(
                f"{settings.GROUP_SERVICE_URL}/api/users/{user_id}/groups/",
                headers={'Authorization': f'Bearer {settings.GROUP_SERVICE_TOKEN}'}
            )
            response.raise_for_status()
            return [group['id'] for group in response.json()]
        except requests.RequestException:
            return []