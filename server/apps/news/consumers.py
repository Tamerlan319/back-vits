from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.core.serializers.json import DjangoJSONEncoder
from .models import News
from .serializers import NewsSerializer

class NewsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.news_group = 'news_updates'
        
        # Присоединяемся к группе
        await self.channel_layer.group_add(
            self.news_group,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Покидаем группу
        await self.channel_layer.group_discard(
            self.news_group,
            self.channel_name
        )

    # Получаем сообщение от группы
    async def news_update(self, event):
        # Отправляем сообщение WebSocket
        await self.send(text_data=json.dumps(event, cls=DjangoJSONEncoder))

    @staticmethod
    def get_news_data(news_id=None):
        if news_id:
            news = News.objects.get(id=news_id)
            serializer = NewsSerializer(news)
        else:
            news = News.objects.filter(is_published=True).order_by('-created_at')[:3]
            serializer = NewsSerializer(news, many=True)
        return serializer.data