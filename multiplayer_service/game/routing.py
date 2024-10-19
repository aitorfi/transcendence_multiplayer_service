from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/game/<str:game_type>/<int:game_id>/", consumers.GameMatchmakingConsumer.as_asgi()),

]
