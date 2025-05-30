import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Application

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if isinstance(self.user, AnonymousUser):
            await self.close()
        else:
            self.group_name = f'user_{self.user.id}'
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def notify_user(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': message,
            'application_id': event.get('application_id'),
            'status': event.get('status')
        }))

    @database_sync_to_async
    def get_application(self, application_id):
        try:
            return Application.objects.get(id=application_id)
        except Application.DoesNotExist:
            return None

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'mark_as_read':
            await self.mark_notifications_as_read()

    @database_sync_to_async
    def mark_notifications_as_read(self):
        self.user.has_unread_applications = False
        self.user.save()