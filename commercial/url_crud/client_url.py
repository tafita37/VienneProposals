from django.urls import path

from commercial.controllers.CRUDController import delete_client, edit_client_page, liste_client_page, new_client_page, save_client, update_client

urlpatterns = [
    path('list/', liste_client_page, name='liste_client_page'),
    path('new/', new_client_page, name='new_client_page'),
    path('save/', save_client, name='save_client'),
    path('update/', update_client, name='update_client'),
    path('edit/<int:client_id>/', edit_client_page, name='edit_client_page'),
    path('delete/', delete_client, name='delete_client')
]