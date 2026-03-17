from django.db import models
from authentification.models import User, Role  # importe tes modèles existants

class UserRole(models.Model):
    id = models.AutoField(primary_key=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, db_column='role_id')
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')

    class Meta:
        db_table = 'user_role'
        unique_together = ('role', 'user')  # optionnel si tu veux empêcher les doublons