import os
from django.core.asgi import get_asgi_application
from server.settings.environments.base import DEBUG_SOCKETS

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings.environments.base')

django_asgi_app = get_asgi_application()

if DEBUG_SOCKETS:
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.auth import AuthMiddlewareStack
    from applications.routing import websocket_urlpatterns
    
    application = ProtocolTypeRouter({
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        ),
    })
else:
    application = django_asgi_app