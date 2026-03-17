from django.db import models

class Role(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30, unique=True)

    class Meta:
        db_table = 'role'