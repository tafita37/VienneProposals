from django.db import models

from commercial.metier.Category import Category


class ExcelImport(models.Model):
	id = models.AutoField(primary_key=True)
	name = models.CharField(max_length=50)
	date_import = models.DateField()
	product_count = models.IntegerField()
	category = models.ForeignKey(Category, on_delete=models.PROTECT, db_column='category_id')

	class Meta:
		db_table = 'excel_import'
