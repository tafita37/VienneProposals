from django.db import models
from commercial.metier.Client import Client
from authentification.metier.User import User

class CommercialProposal(models.Model):
	id = models.AutoField(primary_key=True)
	commercial_proposal_number = models.CharField(max_length=50, unique=True)
	project_name=models.CharField(max_length=100, unique=True)
	installation_address=models.CharField(max_length=100, unique=True)
	date_proposal = models.DateField()
	amount_ht = models.FloatField()  # DOUBLE PRECISION en SQL
	amount_ttc = models.FloatField()  # DOUBLE PRECISION en SQL
	client = models.ForeignKey(Client, on_delete=models.PROTECT, db_column='client_id')
	commercial=models.ForeignKey(User, on_delete=models.PROTECT, db_column='commercial_id')
	state=models.IntegerField(default=1)  # 0: brouillon, 1: validé
	expiration_date = models.DateField(null=True, blank=True)
	no_included = models.TextField()
	cgv = models.TextField()
 
	def save(self, *args, **kwargs):
		if self.pk is None:  # Vérification directe sans variable
			# C'est un nouvel objet
			super().save(*args, **kwargs)
			year = str(self.date_proposal.year)
			reversed_year = year[::-1]
			formatted_id = str(self.pk).zfill(4)
			self.commercial_proposal_number = f"{reversed_year}{formatted_id}"
			super().save(update_fields=['commercial_proposal_number'])
		else:
			super().save(*args, **kwargs)

	@property
	def proposal_product_list(self):
		return list(self.proposal_products.all())

	class Meta:
		db_table = 'commercial_proposal'
