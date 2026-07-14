from django.db import models
from authentification.metier.User import User
from django.db.models.functions import Now

class CommercialChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    commercial=models.ForeignKey(User, on_delete=models.PROTECT, db_column='commercial_id')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())

    class Meta:
        db_table = 'commercial_chat_message'
        ordering = ['created_at'] # Les messages sortiront toujours dans l'ordre chronologique