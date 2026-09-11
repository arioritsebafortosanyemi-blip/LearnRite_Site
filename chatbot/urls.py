from django.urls import path

from chatbot import views

urlpatterns = [
    path('chat/', views.chat, name='chatbot_chat'),
]
