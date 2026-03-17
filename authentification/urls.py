from django.urls import path

from authentification.controllers.UserController import login_user_page

urlpatterns = [
    path('login_page/', login_user_page, name='login_user_page'),
]