from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    id = models.AutoField(primary_key=True)

    first_name = models.CharField(max_length=100, db_column='first_name')
    last_name = models.CharField(max_length=100, db_column='last_name')
    email = models.EmailField(unique=True, db_column='email')
    password = models.TextField(db_column='password')
    failed_login_attempts = models.IntegerField(default=0, db_column='failed_login_attempts')
    # must_change_password = models.BooleanField(default=True)
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'users'