from django.urls import path

from commercial.controllers.CRUDController import delete_supplier, liste_supplier_page, save_supplier

urlpatterns = [
    path('list/', liste_supplier_page, name='liste_supplier_page'),
    path('save/', save_supplier, name='save_supplier'),
    path('delete/', delete_supplier, name='delete_supplier')
]
