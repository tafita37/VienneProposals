from django.db import models
from django.utils import timezone

from commercial.metier.Product import Product
from commercial.metier.Supplier import Supplier


class ProductMovement(models.Model):
    MOVEMENT_TYPE_ENTRY = 'entry'
    MOVEMENT_TYPE_EXIT = 'exit'
    MOVEMENT_TYPE_CHOICES = (
        (MOVEMENT_TYPE_ENTRY, 'Entrée'),
        (MOVEMENT_TYPE_EXIT, 'Sortie'),
    )

    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        db_column='product_id',
        related_name='movements'
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        db_column='supplier_id',
        related_name='product_movements',
        null=True,
        blank=True
    )
    quantity = models.FloatField(null=True, blank=True)  # DOUBLE PRECISION en SQL
    price = models.FloatField()  # DOUBLE PRECISION en SQL
    movement_date = models.DateField(default=timezone.localdate)  # DATE en SQL
    movement_type = models.CharField(max_length=5, choices=MOVEMENT_TYPE_CHOICES)  # 'entry' ou 'exit'

    class Meta:
        db_table = 'product_movement'
