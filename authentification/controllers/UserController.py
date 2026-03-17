# views.py
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

@require_GET
def login_user_page(request):
    if request.user.is_authenticated:
        return redirect('tresorerie_page')  # Redirige si déjà connecté
    return render(request, "views/login_user.html")

@require_POST
def login_user(request):
    user = authenticate(
        request,
        username = request.POST.get('username'),
        password = request.POST.get('password')
    )
    if user:
        login(request, user)
        return redirect('tresorerie_page')
    else :
        messages.error(request, "Nom d’utilisateur ou mot de passe incorrect")
        return redirect('login_user_page')

@require_GET
def logout_user(request):
    logout(request)
    return redirect('login_user_page')