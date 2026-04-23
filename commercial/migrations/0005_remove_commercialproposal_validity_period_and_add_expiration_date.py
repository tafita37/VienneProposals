from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commercial', '0004_alter_category_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='commercialproposal',
            name='validity_period',
        ),
        migrations.AddField(
            model_name='commercialproposal',
            name='expiration_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
