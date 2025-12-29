from django.urls import path, re_path
from .consumers import ProgressConsumer

websocket_urlpatterns = [
    path("ws/progress/<int:server_id>/", ProgressConsumer.as_asgi()),
]
