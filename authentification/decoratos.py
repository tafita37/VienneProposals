# decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from authentification.metier.AdminUser import AdminUser
from authentification.metier.User import User

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


def user_required(view_func):
    """
    Décorateur pour restreindre l'accès aux utilisateurs standards (table users)
    """
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Veuillez vous connecter")
            return redirect('login_user_page')

        if not isinstance(request.user, User):
            messages.error(request, "Accès réservé aux utilisateurs")
            return redirect('login_user_page')

        return view_func(request, *args, **kwargs)

    return wrapped