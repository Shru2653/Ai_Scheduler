from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_ui, name='chat-ui'),
    path('chat/', views.chat, name='chat-api'),
]