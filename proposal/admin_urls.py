"""
URL configuration for proposal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import include, path

from authentification.controllers.UserController import login_admin, login_admin_page
from commercial.controllers.StatController import admin_page, dashboard_page

urlpatterns = [
    path('login_admin_page/', login_admin_page, name='login_admin_page'),
    path('login_admin/', login_admin, name='login_admin'),
    path('dashboard_page/', dashboard_page, name='dashboard_page'),
    path('administration_page/', admin_page, name='admin_page'),
    path('client/', include('commercial.url_crud.client_url')),
    path('user/', include('authentification.url_crud.user_url')),
]
