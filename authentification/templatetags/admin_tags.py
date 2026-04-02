from django import template
from django.utils import timezone
from django.contrib.auth.models import User

register = template.Library()

@register.simple_tag(takes_context=True)
def admin_sidebar_data(context):
    """Charge TOUTES les données pour baseAdmin.html"""
    request = context.get('request')
    
    # Structure de données par défaut
    data = {
        'name': 'Admin',
        'first_letter': 'A'
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
    
    # Structure de données par défaut
    data = {
        'name': 'Utilisateur',
        'first_letter': 'U'
    }
    
    # Si utilisateur connecté, on charge les vraies données
    if request and request.user.is_authenticated:
        data['name'] = request.user.first_name
        data['first_letter'] = request.user.first_name[0].upper() if request.user.first_name else 'A'
    
    return data