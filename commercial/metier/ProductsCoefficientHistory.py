from django.db import models

class ProductsCoefficientHistory(models.Model):
    id = models.AutoField(primary_key=True)
    coefficient = models.DecimalField(max_digits=15, decimal_places=2)  # NUMERIC(15,2)
    date_change = models.DateField(auto_now_add=True)  # DATE en SQL
    
    class Meta:
        db_table = 'products_coefficient_history'