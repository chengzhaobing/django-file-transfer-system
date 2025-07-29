from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/file-updates/$', consumers.FileUpdateConsumer.as_asgi()),
    re_path(r'ws/lan-discovery/$', consumers.LANDiscoveryConsumer.as_asgi()),
]