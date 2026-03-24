from django.urls import path

from commercial.controllers.CRUDController import delete_category, liste_categorie_page, saveCategorie

urlpatterns = [
    path('list/', liste_categorie_page, name='liste_categorie_page'),
    path('save/', saveCategorie, name='save_categorie'),
    path('delete/', delete_category, name='delete_categorie')
]