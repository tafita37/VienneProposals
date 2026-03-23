from django.db import models

from commercial.metier.Unit import Unit
from commercial.metier.Category import Category

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    designation = models.TextField(unique=True)
    purchase_unit_price = models.FloatField()  # DOUBLE PRECISION en SQL
    sale_unit_price = models.FloatField()  # DOUBLE PRECISION en SQL
    coefficient = models.DecimalField(max_digits=15, decimal_places=2)  # NUMERIC(15,2)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, db_column='unit_id')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, db_column='category_id')

    class Meta:
        db_table = 'product'