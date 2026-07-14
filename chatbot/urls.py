from django.urls import include, path

from chatbot.controllers.ChatController import chatbot_response_admin, chatbot_response_commercial

urlpatterns = [
    path('api/chatbot/admin/', chatbot_response_admin, name='chatbot_response_admin'),
    path('api/chatbot/commercial/', chatbot_response_commercial, name='chatbot_response_commercial'),
]