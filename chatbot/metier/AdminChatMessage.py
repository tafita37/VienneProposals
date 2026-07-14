from django.db import models
from authentification.metier.AdminUser import AdminUser
from django.db.models.functions import Now

class AdminChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    admin=models.ForeignKey(AdminUser, on_delete=models.PROTECT, db_column='admin_id')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())

    class Meta:
        db_table = 'admin_chat_message'
        ordering = ['created_at'] # Les messages sortiront toujours dans l'ordre chronologique