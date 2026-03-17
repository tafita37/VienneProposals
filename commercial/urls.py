from django.urls import path

from commercial.controllers.StatController import dashboard_page

urlpatterns = [
    path('dashboard_page/', dashboard_page, name='dashboard_page'),
]