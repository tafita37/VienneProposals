# views.py
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import IntegrityError

from authentification.backends import AdminUserBackend
from authentification.decoratos import admin_required
from authentification.models import Role, User, UserRole

@require_GET
def login_user_page(request):
    if request.user.is_authenticated:
        return redirect('catalogue_page')  # Redirige si déjà connecté
    return render(request, "views/login_user.html")

@require_GET
def login_admin_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard_page')  # Redirige si déjà connecté
    return render(request, "views/login_admin.html")

@require_POST
def login_user(request):
    user = authenticate(
        request,
        username = request.POST.get('username'),
        password = request.POST.get('password')
    )
    if user:
        login(request, user)
        return redirect('catalogue_page')
    else :
        messages.error(request, "Nom d’utilisateur ou mot de passe incorrect")
        return redirect('login_user_page')
    
@require_POST
def login_admin(request):
    backend = AdminUserBackend()
    user = backend.authenticate(
        request,
        username = request.POST.get('username'),
        password = request.POST.get('password')
    )
    if user:
        login(request, user, backend='authentification.backends.AdminUserBackend')
        return redirect('dashboard_page')
    else :
        messages.error(request, "Nom d’utilisateur ou mot de passe incorrect")
        return redirect('login_admin_page')

@require_GET
def logout_user(request):
    logout(request)
    return redirect('login_user_page')


@require_GET
@admin_required
def list_users_admin_page(request):
    users = User.objects.filter(is_active=True).prefetch_related('userrole_set__role').order_by('username')
    return render(
        request,
        'views/admin_users.html',
        {'users': users}
    )


@require_GET
@admin_required
def new_user_admin_page(request):
    roles = Role.objects.all().order_by('name')
    return render(
        request,
        'views/admin_user_create.html',
        {'roles': roles}
    )


@require_GET
@admin_required
def edit_user_admin_page(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if not user:
        messages.error(request, "Utilisateur introuvable")
        return redirect('list_users_admin_page')

    roles = Role.objects.all().order_by('name')
    selected_role_ids = set(
        UserRole.objects.filter(user=user).values_list('role_id', flat=True)
    )
    return render(
        request,
        'views/admin_user_edit.html',
        {
            'user_item': user,
            'roles': roles,
            'selected_role_ids': selected_role_ids,
        }
    )


@require_POST
@admin_required
def save_user_admin(request):
    username = (request.POST.get('username') or '').strip()
    first_name = (request.POST.get('first_name') or '').strip()
    last_name = (request.POST.get('last_name') or '').strip()
    email = (request.POST.get('email') or '').strip()
    password = request.POST.get('password') or ''
    role_ids = request.POST.getlist('role_ids')

    if not username or not first_name or not last_name or not email or not password:
        messages.error(request, "Tous les champs obligatoires doivent etre remplis")
        return redirect('new_user_admin_page')

    try:
        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        user.set_password(password)
        user.save()

        for role_id in role_ids:
            role = Role.objects.filter(id=role_id).first()
            if role:
                UserRole.objects.get_or_create(user=user, role=role)

        messages.success(request, "Utilisateur cree avec succes")
        return redirect('list_users_admin_page')
    except IntegrityError:
        messages.error(request, "Nom d'utilisateur ou email deja utilise")
        return redirect('new_user_admin_page')


@require_POST
@admin_required
def update_user_admin(request):
    user_id = request.POST.get('user_id')
    user = User.objects.filter(id=user_id).first()

    if not user:
        messages.error(request, "Utilisateur introuvable")
        return redirect('list_users_admin_page')

    username = (request.POST.get('username') or '').strip()
    first_name = (request.POST.get('first_name') or '').strip()
    last_name = (request.POST.get('last_name') or '').strip()
    email = (request.POST.get('email') or '').strip()
    password = request.POST.get('password') or ''
    role_ids = request.POST.getlist('role_ids')

    if not username or not first_name or not email:
        messages.error(request, "Tous les champs obligatoires doivent etre remplis")
        return redirect('edit_user_admin_page', user_id=user.id)

    try:
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        if password.strip():
            user.set_password(password)
        user.save()

        UserRole.objects.filter(user=user).delete()
        for role_id in role_ids:
            role = Role.objects.filter(id=role_id).first()
            if role:
                UserRole.objects.get_or_create(user=user, role=role)

        messages.success(request, "Utilisateur mis a jour avec succes")
        return redirect('list_users_admin_page')
    except IntegrityError:
        messages.error(request, "Nom d'utilisateur ou email deja utilise")
        return redirect('edit_user_admin_page', user_id=user.id)


@require_GET
@admin_required
def delete_user_admin(request):
    user_id = request.GET.get('id')
    user = User.objects.filter(id=user_id).first()
    if not user:
        messages.error(request, "Utilisateur introuvable")
        return redirect('list_users_admin_page')

    if not user.is_active:
        messages.info(request, "Utilisateur deja desactive")
        return redirect('list_users_admin_page')

    user.is_active = False
    user.save(update_fields=['is_active'])
    messages.success(request, "Utilisateur desactive avec succes")
    return redirect('list_users_admin_page')