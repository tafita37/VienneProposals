from django.db import models

from commercial.metier.CommercialProposal import CommercialProposal
from commercial.metier.Product import Product


class ProposalProduct(models.Model):
    id = models.AutoField(primary_key=True)
    coefficient = models.FloatField()  # DOUBLE PRECISION en SQL
    quantity = models.FloatField()  # DOUBLE PRECISION en SQL
    purchase_unit_price = models.FloatField()  # DOUBLE PRECISION en SQL
    sale_unit_price = models.FloatField()  # DOUBLE PRECISION en SQL
    commercial_proposal = models.ForeignKey(
        CommercialProposal,
        on_delete=models.PROTECT,
        db_column='commercial_proposal_id',
        related_name='proposal_products'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        db_column='product_id',
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'proposal_product'
