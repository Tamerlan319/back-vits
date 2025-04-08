from rest_framework import serializers
from .models import Event, Group
from .cors.services import GroupService

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']

class EventSerializer(serializers.ModelSerializer):
    group_name = serializers.SerializerMethodField(read_only=True)
    group_id = serializers.IntegerField(write_only=True)
    first_name = serializers.CharField(source='creator.first_name', read_only=True)
    last_name = serializers.CharField(source='creator.last_name', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'start_time', 'end_time',
            'event_type', 'group_id', 'group_name', 'is_recurring',
            'recurrence_rule', 'first_name', 'last_name'
        ]
        extra_kwargs = {
            'creator': {'read_only': True}
        }

    def get_group_name(self, obj):
        if not obj.group_id:
            return None
        group = GroupService.get_group(obj.group_id)
        return group.get('name') if group else None