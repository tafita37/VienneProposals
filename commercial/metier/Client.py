from django.db import models


class Client(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    website_url = models.TextField(unique=True)
    phone = models.CharField(max_length=50, unique=True)
    is_company = models.BooleanField(null=False)

    class Meta:
        db_table = 'client'
