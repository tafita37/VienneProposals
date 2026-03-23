from django.urls import path

from commercial.controllers.CommercialController import appercu_proposition_page, catalogue_page, get_client_by_id_api, get_products_api, new_proposition_page, proposition_detail, propositions_page, remove_selected_product_api, save_proposal_options_api, save_selected_products_api, validate_proposition_page
from commercial.controllers.StatController import dashboard_page

urlpatterns = [
    path('dashboard_page/', dashboard_page, name='dashboard_page'),
    path('catalog_page/', catalogue_page, name='catalogue_page'),
    path('api/products/', get_products_api, name='get_products_api'),
    path('api/clients/<int:client_id>/', get_client_by_id_api, name='get_client_by_id_api'),
    path('api/proposals/selected-products/', save_selected_products_api, name='save_selected_products_api'),
    path('api/proposals/remove-product/', remove_selected_product_api, name='remove_selected_product_api'),
    path('api/proposals/options/', save_proposal_options_api, name='save_proposal_options_api'),
    path('new_proposition_page/', new_proposition_page, name='new_proposition_page'),
    path('preview_proposition_page/', appercu_proposition_page, name='appercu_proposition_page'),
    path('validate_proposition_page/', validate_proposition_page, name='validate_proposition_page'),
    path('propositions_page/', propositions_page, name='propositions_page'),
    path('proposition_detail/', proposition_detail, name='proposition_detail_page'),
]