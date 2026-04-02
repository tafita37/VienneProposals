# backends.py
from django.contrib.auth.backends import BaseBackend
from .models import AdminUser

class AdminUserBackend(BaseBackend):
    """
    Backend pour les administrateurs (table séparée)
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = AdminUser.objects.get(username=username)
            if user.check_password(password):
                return user
        except AdminUser.DoesNotExist:
            return None
        
        return None
    
    def get_user(self, user_id):
        try:
            return AdminUser.objects.get(pk=user_id)
        except AdminUser.DoesNotExist:
            return None