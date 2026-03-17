from django.urls import path

from authentification.controllers.UserController import login_user, login_user_page, logout_user

urlpatterns = [
    path('login_page/', login_user_page, name='login_user_page'),
    path('login_user/', login_user, name='login_user'),
    path('logout_user/', logout_user, name='logout_user'),
]