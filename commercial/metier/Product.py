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
    categories = models.ManyToManyField(
        Category,
        through='ProductCategory',
        related_name='products',
        blank=True,
    )

    @property
    def category(self):
        return self.categories.order_by('id').first()

    @property
    def category_id(self):
        category = self.category
        return category.id if category else None

    @property
    def category_name(self):
        category = self.category
        return category.name if category else ''

    @property
    def category_names(self):
        return ', '.join(self.categories.order_by('name').values_list('name', flat=True))

    @property
    def category_ids(self):
        return list(self.categories.order_by('id').values_list('id', flat=True))

    @property
    def category_ids_csv(self):
        return ','.join(str(category_id) for category_id in self.category_ids)

    class Meta:
        db_table = 'product'