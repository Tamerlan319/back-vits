from server.apps.users.models import Group, User

class GroupService:
    @staticmethod
    def get_group(group_id):
        """Получает информацию о группе из локальной БД"""
        try:
            group = Group.objects.get(pk=group_id)
            return {
                'id': group.id,
                'name': group.name,
                # Другие необходимые поля
            }
        except Group.DoesNotExist:
            return None

    @staticmethod
    def get_group_members(group_id, role=None):
        """Получает список ID участников группы"""
        try:
            group = Group.objects.get(pk=group_id)
            members = group.members.all()
            if role:
                members = members.filter(role=role)
            return list(members.values_list('id', flat=True))
        except Group.DoesNotExist:
            return []

    @staticmethod
    def get_user_groups(user_id):
        """Получает список ID групп пользователя"""
        try:
            user = User.objects.get(pk=user_id)
            return list(user.groups.values_list('id', flat=True))
        except User.DoesNotExist:
            return []

    @staticmethod
    def validate_group_exists(group_id):
        """Проверяет существование группы"""
        return Group.objects.filter(pk=group_id).exists()