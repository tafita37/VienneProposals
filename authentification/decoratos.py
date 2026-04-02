# decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from authentification.models import AdminUser

def admin_required(view_func):
    """
    Décorateur pour restreindre l'accès aux administrateurs (table admin_users)
    """
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Veuillez vous connecter")
            return redirect('login_admin_page')
        
        # Vérifie si l'utilisateur est un AdminUser (table admin_users)
        if not isinstance(request.user, AdminUser):
            messages.error(request, "Accès réservé aux administrateurs")
            return redirect('login_admin_page')
        
        return view_func(request, *args, **kwargs)
    
    return wrapped