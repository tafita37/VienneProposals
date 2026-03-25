from django.urls import path

from commercial.controllers.CRUDController import delete_product, liste_product_page, saveProduct


urlpatterns = [
    path('list/', liste_product_page, name='liste_product_page'),
    path('save/', saveProduct, name='saveProduct'),
    path('delete/', delete_product, name='delete_product'),
]