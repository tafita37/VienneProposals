from django.urls import path

from authentification.controllers.UserController import (
    delete_user_admin,
    edit_user_admin_page,
    list_users_admin_page,
    new_user_admin_page,
    save_user_admin,
    update_user_admin,
)

urlpatterns = [
    path('list/', list_users_admin_page, name='list_users_admin_page'),
    path('new/', new_user_admin_page, name='new_user_admin_page'),
    path('save/', save_user_admin, name='save_user_admin'),
    path('edit/<int:user_id>/', edit_user_admin_page, name='edit_user_admin_page'),
    path('update/', update_user_admin, name='update_user_admin'),
    path('delete/', delete_user_admin, name='delete_user_admin'),
]
