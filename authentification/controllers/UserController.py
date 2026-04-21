# views.py
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.core import signing
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.contrib.auth import update_session_auth_hash

from authentification.backends import AdminUserBackend
from authentification.decoratos import admin_required
from authentification.decoratos import user_required
from authentification.metier.AdminUser import AdminUser
from authentification.models import Role, User, UserRole

import logging
logger = logging.getLogger(__name__)

PASSWORD_TOKEN_MAX_AGE = 604800
PASSWORD_TOKEN_SALT = 'password-reset-v1'


def _build_password_token(user_id, account_type, purpose):
    return signing.dumps(
        {
            'user_id': int(user_id),
            'account_type': account_type,
            'purpose': purpose,
        },
        salt=PASSWORD_TOKEN_SALT,
    )


def _read_password_token(token, expected_account_type, expected_purpose):
    payload = signing.loads(
        token,
        salt=PASSWORD_TOKEN_SALT,
        max_age=PASSWORD_TOKEN_MAX_AGE,
    )

    if payload.get('account_type') != expected_account_type:
        raise signing.BadSignature('Type de compte invalide')
    if payload.get('purpose') != expected_purpose:
        raise signing.BadSignature('Objectif de token invalide')

    return payload.get('user_id')

@require_GET
def login_user_page(request):
    if request.user.is_authenticated and isinstance(request.user, User):
        return redirect('catalogue_page')  # Redirige si déjà connecté
    if request.user.is_authenticated and isinstance(request.user, AdminUser):
        return redirect('dashboard_page')
    return render(request, "views/login_user.html")

@require_GET
def login_admin_page(request):
    if request.user.is_authenticated and isinstance(request.user, AdminUser):
        return redirect('dashboard_page')  # Redirige si déjà connecté
    if request.user.is_authenticated and isinstance(request.user, User):
        return redirect('catalogue_page')
    return render(request, "views/login_admin.html")

@require_POST
def login_user(request):
    user = authenticate(
        request,
        username = request.POST.get('username'),
        password = request.POST.get('password'),
        backend='django.contrib.auth.backends.ModelBackend'
    )
    if user and isinstance(user, User):
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
def forgot_password_user_page(request):
    return render(request, "views/forgot_password_user.html")


@require_POST
def send_user_reset_link(request):
    email = (request.POST.get('email') or '').strip().lower()
    if not email:
        messages.error(request, "Veuillez saisir votre adresse email")
        return redirect('forgot_password_user_page')

    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user:
        token = _build_password_token(user.id, 'user', 'forgot_password')
        reset_url = request.build_absolute_uri(
            f"{reverse('reset_user_password_page')}?token={token}"
        )
        send_mail(
            subject="Réinitialisation de votre mot de passe",
            message=(
                f"Bonjour {user.first_name} {user.last_name},\n\n"
                "Vous avez demandé la réinitialisation de votre mot de passe.\n"
                "Utilisez le lien suivant:\n"
                f"{reset_url}\n\n"
                "Ce lien est valide pendant 7 jours.\n"
                "Si vous n'etes pas à l'origine de cette demande, ignorez cet email.\n"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

    messages.success(request, "Si le compte existe, un lien de réinitialisation a été envoyé")
    return redirect('login_user_page')


@require_GET
def reset_user_password_page(request):
    token = (request.GET.get('token') or '').strip()
    if not token:
        messages.error(request, "Lien invalide")
        return redirect('login_user_page')

    try:
        user_id = _read_password_token(token, 'user', 'forgot_password')
    except signing.BadSignature:
        messages.error(request, "Lien invalide ou expiré")
        return redirect('login_user_page')

    user = User.objects.filter(id=user_id, is_active=True).first()
    if not user:
        messages.error(request, "Utilisateur introuvable")
        return redirect('login_user_page')

    return render(request, "views/reset_password_user.html", {'token': token, 'username': user.username})


@require_POST
def reset_user_password(request):
    token = (request.POST.get('token') or '').strip()
    new_password = (request.POST.get('new_password') or '').strip()
    confirm_password = (request.POST.get('confirm_password') or '').strip()

    if not token:
        messages.error(request, "Lien invalide")
        return redirect('login_user_page')

    try:
        user_id = _read_password_token(token, 'user', 'forgot_password')
    except signing.BadSignature:
        messages.error(request, "Lien invalide ou expiré")
        return redirect('login_user_page')

    user = User.objects.filter(id=user_id, is_active=True).first()
    if not user:
        messages.error(request, "Utilisateur introuvable")
        return redirect('login_user_page')

    if not new_password or not confirm_password:
        messages.error(request, "Veuillez remplir tous les champs")
        return render(request, "views/reset_password_user.html", {'token': token, 'username': user.username})

    if new_password != confirm_password:
        messages.error(request, "Les mots de passe ne correspondent pas")
        return render(request, "views/reset_password_user.html", {'token': token, 'username': user.username})

    if len(new_password) < 8:
        messages.error(request, "Le mot de passe doit contenir au moins 8 caractères")
        return render(request, "views/reset_password_user.html", {'token': token, 'username': user.username})

    user.set_password(new_password)
    user.save(update_fields=['password'])

    messages.success(request, "Mot de passe mis à jour avec succès")
    return redirect('login_user_page')


@require_GET
@user_required
def change_user_password_page(request):
    return render(request, "views/change_password_user.html")


@require_POST
@user_required
def change_user_password(request):
    current_password = (request.POST.get('current_password') or '').strip()
    new_password = (request.POST.get('new_password') or '').strip()
    confirm_password = (request.POST.get('confirm_password') or '').strip()

    if not request.user.check_password(current_password):
        messages.error(request, "Le mot de passe actuel est incorrect")
        return render(request, "views/change_password_user.html")

    if not new_password or not confirm_password:
        messages.error(request, "Veuillez remplir tous les champs")
        return render(request, "views/change_password_user.html")

    if new_password != confirm_password:
        messages.error(request, "Les mots de passe ne correspondent pas")
        return render(request, "views/change_password_user.html")

    if len(new_password) < 8:
        messages.error(request, "Le mot de passe doit contenir au moins 8 caractères")
        return render(request, "views/change_password_user.html")

    request.user.set_password(new_password)
    request.user.save(update_fields=['password'])
    update_session_auth_hash(request, request.user)

    messages.success(request, "Mot de passe modifié avec succès")
    return redirect('catalogue_page')


@require_GET
@admin_required
def change_admin_password_page(request):
    return render(request, "views/change_password_admin.html")


@require_POST
@admin_required
def change_admin_password(request):
    current_password = (request.POST.get('current_password') or '').strip()
    new_password = (request.POST.get('new_password') or '').strip()
    confirm_password = (request.POST.get('confirm_password') or '').strip()

    if not request.user.check_password(current_password):
        messages.error(request, "Le mot de passe actuel est incorrect")
        return render(request, "views/change_password_admin.html")

    if not new_password or not confirm_password:
        messages.error(request, "Veuillez remplir tous les champs")
        return render(request, "views/change_password_admin.html")

    if new_password != confirm_password:
        messages.error(request, "Les mots de passe ne correspondent pas")
        return render(request, "views/change_password_admin.html")

    if len(new_password) < 8:
        messages.error(request, "Le mot de passe doit contenir au moins 8 caractères")
        return render(request, "views/change_password_admin.html")

    request.user.set_password(new_password)
    request.user.save(update_fields=['password'])
    update_session_auth_hash(request, request.user)

    messages.success(request, "Mot de passe administrateur modifié avec succès")
    return redirect('dashboard_page')


@require_GET
def define_password_page(request):
    token = (request.GET.get('token') or '').strip()
    if not token:
        messages.error(request, "Lien invalide")
        return redirect('login_user_page')

    try:
        user_id = _read_password_token(token, 'user', 'define_password')
    except signing.BadSignature:
        messages.error(request, "Lien invalide ou expiré")
        return redirect('login_user_page')

    user = User.objects.filter(id=user_id, is_active=True).first()
    if not user:
        messages.error(request, "Utilisateur introuvable")
        return redirect('login_user_page')

    return render(request, "views/set_password.html", {'token': token, 'username': user.username})


@require_POST
def define_password(request):
    token = (request.POST.get('token') or '').strip()
    new_password = (request.POST.get('new_password') or '').strip()
    confirm_password = (request.POST.get('confirm_password') or '').strip()

    if not token:
        messages.error(request, "Lien invalide")
        return redirect('login_user_page')

    try:
        user_id = _read_password_token(token, 'user', 'define_password')
    except signing.BadSignature:
        messages.error(request, "Lien invalide ou expiré")
        return redirect('login_user_page')

    user = User.objects.filter(id=user_id, is_active=True).first()
    if not user:
        messages.error(request, "Utilisateur introuvable")
        return redirect('login_user_page')

    if not new_password or not confirm_password:
        messages.error(request, "Veuillez remplir tous les champs")
        return render(request, "views/set_password.html", {'token': token, 'username': user.username})

    if new_password != confirm_password:
        messages.error(request, "Les mots de passe ne correspondent pas")
        return render(request, "views/set_password.html", {'token': token, 'username': user.username})

    if len(new_password) < 8:
        messages.error(request, "Le mot de passe doit contenir au moins 8 caractères")
        return render(request, "views/set_password.html", {'token': token, 'username': user.username})

    user.set_password(new_password)
    user.save(update_fields=['password'])

    messages.success(request, "Mot de passe défini avec succès. Vous pouvez vous connecter")
    return redirect('login_user_page')

@require_GET
def forgot_password_admin_page(request):
    return render(request, "views/forgot_password_admin.html")


@require_POST
def send_admin_reset_link(request):
    email = (request.POST.get('email') or '').strip().lower()
    if not email:
        messages.error(request, "Veuillez saisir votre adresse email administrateur")
        return redirect('forgot_password_admin_page')

    admin_user = AdminUser.objects.filter(email__iexact=email).first()
    if admin_user:
        token = _build_password_token(admin_user.id, 'admin', 'forgot_password')
        reset_url = request.build_absolute_uri(
            f"{reverse('reset_admin_password_page')}?token={token}"
        )

        send_mail(
            subject="Réinitialisation du mot de passe administrateur",
            message=(
                f"Bonjour {admin_user.first_name} {admin_user.last_name},\n\n"
                "Une demande de réinitialisation du mot de passe administrateur a été reçue.\n"
                "Utilisez le lien suivant:\n"
                f"{reset_url}\n\n"
                "Ce lien est valide pendant 7 jours.\n"
                "Si vous n'etes pas à l'origine de cette demande, ignorez cet email.\n"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_user.email],
            fail_silently=False,
        )

    messages.success(request, "Si le compte existe, un lien de réinitialisation a été envoyé")
    return redirect('login_admin_page')


@require_GET
def reset_admin_password_page(request):
    token = (request.GET.get('token') or '').strip()
    if not token:
        messages.error(request, "Lien invalide")
        return redirect('login_admin_page')

    try:
        admin_user_id = _read_password_token(token, 'admin', 'forgot_password')
    except signing.BadSignature:
        messages.error(request, "Lien invalide ou expiré")
        return redirect('login_admin_page')

    admin_user = AdminUser.objects.filter(id=admin_user_id).first()
    if not admin_user:
        messages.error(request, "Administrateur introuvable")
        return redirect('login_admin_page')

    return render(request, "views/reset_password_admin.html", {'token': token, 'username': admin_user.username})


@require_POST
def reset_admin_password(request):
    token = (request.POST.get('token') or '').strip()
    new_password = (request.POST.get('new_password') or '').strip()
    confirm_password = (request.POST.get('confirm_password') or '').strip()

    if not token:
        messages.error(request, "Lien invalide")
        return redirect('login_admin_page')

    try:
        admin_user_id = _read_password_token(token, 'admin', 'forgot_password')
    except signing.BadSignature:
        messages.error(request, "Lien invalide ou expiré")
        return redirect('login_admin_page')

    admin_user = AdminUser.objects.filter(id=admin_user_id).first()
    if not admin_user:
        messages.error(request, "Administrateur introuvable")
        return redirect('login_admin_page')

    if not new_password or not confirm_password:
        messages.error(request, "Veuillez remplir tous les champs")
        return render(request, "views/reset_password_admin.html", {'token': token, 'username': admin_user.username})

    if new_password != confirm_password:
        messages.error(request, "Les mots de passe ne correspondent pas")
        return render(request, "views/reset_password_admin.html", {'token': token, 'username': admin_user.username})

    if len(new_password) < 8:
        messages.error(request, "Le mot de passe doit contenir au moins 8 caractères")
        return render(request, "views/reset_password_admin.html", {'token': token, 'username': admin_user.username})

    admin_user.set_password(new_password)
    admin_user.save(update_fields=['password'])

    messages.success(request, "Mot de passe administrateur mis à jour avec succès")
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
    role_ids = request.POST.getlist('role_ids')

    if not username or not first_name or not last_name or not email:
        messages.error(request, "Tous les champs obligatoires doivent etre remplis")
        return redirect('new_user_admin_page')

    try:
        # Exclude ambiguous chars for easier manual typing.
        generated_password = get_random_string(
            12,
            allowed_chars='ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%&*?'
        )

        with transaction.atomic():
            user = User(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
            )
            user.set_password(generated_password)
            user.save()

            setup_token = _build_password_token(user.id, 'user', 'define_password')
            setup_url = request.build_absolute_uri(
                f"{reverse('define_password_page')}?token={setup_token}"
            )

            for role_id in role_ids:
                role = Role.objects.filter(id=role_id).first()
                if role:
                    UserRole.objects.get_or_create(user=user, role=role)

            send_mail(
                subject="Vos identifiants Vienne Agencement",
                message=(
                    f"Bonjour {first_name} {last_name},\n\n"
                    "Votre compte utilisateur vient d'etre cree.\n"
                    f"Nom d'utilisateur: {username}\n"
                    "Pour definir votre mot de passe, cliquez sur le lien suivant:\n"
                    f"{setup_url}\n\n"
                    "Ce lien est valide pendant 7 jours.\n"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

        messages.success(request, "Utilisateur cree avec succes")
        return redirect('list_users_admin_page')
    except IntegrityError:
        messages.error(request, "Nom d'utilisateur ou email deja utilise")
        return redirect('new_user_admin_page')
    except Exception as e:
        messages.error(request, "Utilisateur non cree: impossible d'envoyer l'email d'acces")
        logger.error(f"ERREUR EMAIL: {repr(e)}")
        logger.error(f"TYPE: {type(e).__name__}")
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