from django.db import models
from django.contrib.auth.models import AbstractBaseUser

class AdminUser(AbstractBaseUser):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True, null=False, db_column='username')
    first_name = models.CharField(max_length=100, db_column='first_name')
    last_name = models.CharField(max_length=100, db_column='last_name')
    email = models.EmailField(unique=True, db_column='email')
    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'username'

    class Meta:
        db_table = 'admin_users'