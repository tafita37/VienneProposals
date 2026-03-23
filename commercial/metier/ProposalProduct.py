from django.db import models

from commercial.metier.CommercialProposal import CommercialProposal


class ProposalProduct(models.Model):
    id = models.AutoField(primary_key=True)
    coefficient = models.FloatField()  # DOUBLE PRECISION en SQL
    quantity = models.FloatField()  # DOUBLE PRECISION en SQL
    unit_price = models.FloatField()  # DOUBLE PRECISION en SQL
    commercial_proposal = models.ForeignKey(CommercialProposal, on_delete=models.PROTECT, db_column='commercial_proposal_id')

    class Meta:
        db_table = 'proposal_product'
