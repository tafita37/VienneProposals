from django import template

from chatbot.metier.CommercialChatMessage import CommercialChatMessage
from chatbot.metier.AdminChatMessage import AdminChatMessage

register = template.Library()

@register.simple_tag(takes_context=True)
def admin_sidebar_data(context):
    """Charge TOUTES les données pour baseAdmin.html"""
    request = context.get('request')
    history_message=AdminChatMessage.objects.filter(admin=request.user) if request and request.user.is_authenticated else []
    
    # Structure de données par défaut
    data = {
        'name': 'Admin',
        'first_letter': 'A',
        'history_message': history_message
    }
    
    # Si utilisateur connecté, on charge les vraies données
    if request and request.user.is_authenticated:
        data['name'] = request.user.first_name
        data['first_letter'] = request.user.first_name[0].upper() if request.user.first_name else 'A'
    
    return data

@register.simple_tag(takes_context=True)
def user_sidebar_data(context):
    """Charge TOUTES les données pour baseAdmin.html"""
    request = context.get('request')
    history_message=CommercialChatMessage.objects.filter(commercial=request.user) if request and request.user.is_authenticated else []
    # Structure de données par défaut
    data = {
        'name': 'Utilisateur',
        'first_letter': 'U',
        'history_message': history_message
    }
    
    # Si utilisateur connecté, on charge les vraies données
    if request and request.user.is_authenticated:
        data['name'] = request.user.first_name
        data['first_letter'] = request.user.first_name[0].upper() if request.user.first_name else 'A'
    
    return data