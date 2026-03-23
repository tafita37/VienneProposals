from django.db import models

from commercial.metier.Client import Client
from commercial.metier.CompanyType import CompanyType


class Company(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    registration_number = models.CharField(max_length=50, unique=True)
    tax_identification_number = models.CharField(max_length=50, unique=True)
    created_at = models.DateField()
    company_type = models.ForeignKey(CompanyType, on_delete=models.PROTECT, db_column='company_type_id')
    client = models.ForeignKey(Client, on_delete=models.PROTECT, db_column='client_id')

    class Meta:
        db_table = 'company'
