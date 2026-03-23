from django.db import models

from commercial.metier.Client import Client


class Individual(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField()
    id_card_number = models.CharField(max_length=20, unique=True)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, db_column='client_id')

    class Meta:
        db_table = 'individual'
