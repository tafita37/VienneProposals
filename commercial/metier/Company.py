from django.db import models

from commercial.metier.Client import Client
from commercial.metier.CompanyType import CompanyType


class Company(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    registration_number = models.CharField(max_length=50, unique=True)
    tax_identification_number = models.CharField(max_length=50, unique=True)
    created_at = models.DateField()
    company_type = models.ForeignKey(CompanyType, on_delete=models.PROTECT, db_column='company_type_id')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, db_column='client_id')

    class Meta:
        db_table = 'company'

    def save(self, client_data=None, *args, **kwargs):
        """
        Sauvegarde une Company en créant d'abord un Client associé.
        
        Args:
            client_data (dict): Dictionnaire contenant les informations du client
                - name (str): Nom/Raison sociale
                - address (str): Adresse
                - phone (str): Téléphone
                - email (str): Email
                - website_url (str): URL du site web
        """
        if client_data and not self.client_id:
            # Créer le client associé avec is_company=True
            client = Client.objects.create(
                name=client_data['name'],
                address=client_data['address'],
                phone=client_data['phone'],
                email=client_data['email'],
                website_url=client_data['website_url'],
                is_company=True
            )
            self.client = client
        
        super().save(*args, **kwargs)
