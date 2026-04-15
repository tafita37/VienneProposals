from django.urls import path

from commercial.controllers.CRUDController import delete_product, get_products_api, liste_product_page, saveProduct, update_global_product_coefficient


urlpatterns = [
    path('list/', liste_product_page, name='liste_product_page'),
    path('api/products/', get_products_api, name='get_products_api'),
    path('save/', saveProduct, name='saveProduct'),
    path('update-global-coefficient/', update_global_product_coefficient, name='update_global_product_coefficient'),
    path('delete/', delete_product, name='delete_product'),
]