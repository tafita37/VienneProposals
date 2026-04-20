from django.urls import path

from authentification.controllers.UserController import (
    change_user_password,
    change_user_password_page,
    define_password,
    define_password_page,
    login_user,
    login_user_page,
    logout_user,
)

urlpatterns = [
    path('login_page/', login_user_page, name='login_user_page'),
    path('login_user/', login_user, name='login_user'),
    path('logout_user/', logout_user, name='logout_user'),
    path('define_password_page/', define_password_page, name='define_password_page'),
    path('define_password/', define_password, name='define_password'),
    path('change_password_page/', change_user_password_page, name='change_user_password_page'),
    path('change_password/', change_user_password, name='change_user_password'),
]