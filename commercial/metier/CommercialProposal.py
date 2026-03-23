from django.db import models

from commercial.metier.Client import Client


class CommercialProposal(models.Model):
	id = models.AutoField(primary_key=True)
	date_proposal = models.DateField()
	amount_ht = models.FloatField()  # DOUBLE PRECISION en SQL
	amount_ttc = models.FloatField()  # DOUBLE PRECISION en SQL
	client = models.ForeignKey(Client, on_delete=models.PROTECT, db_column='client_id')

	class Meta:
		db_table = 'commercial_proposal'
