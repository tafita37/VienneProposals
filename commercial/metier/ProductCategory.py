from django.db import models

from commercial.metier.Category import Category
from commercial.metier.Product import Product


class ProductCategory(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='product_id')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, db_column='category_id')

    class Meta:
        db_table = 'product_category'
        unique_together = (('product', 'category'),)