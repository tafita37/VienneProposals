from django.db import models
from commercial.metier.Client import Client
from authentification.metier.User import User

class CommercialProposal(models.Model):
	id = models.AutoField(primary_key=True)
	date_proposal = models.DateField()
	amount_ht = models.FloatField()  # DOUBLE PRECISION en SQL
	amount_ttc = models.FloatField()  # DOUBLE PRECISION en SQL
	client = models.ForeignKey(Client, on_delete=models.PROTECT, db_column='client_id')
	commercial=models.ForeignKey(User, on_delete=models.PROTECT, db_column='commercial_id')
	state=models.IntegerField(default=1)  # 0: brouillon, 1: validé
	validity_period = models.IntegerField(default=30)  # Durée de validité en jours

	@property
	def proposal_product_list(self):
		return list(self.proposal_products.all())

	class Meta:
		db_table = 'commercial_proposal'
