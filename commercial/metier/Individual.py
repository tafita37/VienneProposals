from django.db import models

from commercial.metier.Client import Client


class Individual(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField()
    id_card_number = models.CharField(max_length=20, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, db_column='client_id')

    class Meta:
        db_table = 'individual'

    def save(self, client_data=None, *args, **kwargs):
        """
        Sauvegarde un Individual en créant d'abord un Client associé.
        
        Args:
            client_data (dict): Dictionnaire contenant les informations du client
                - name (str): Nom/Raison sociale
                - address (str): Adresse
                - phone (str): Téléphone
                - email (str): Email
                - website_url (str): URL du site web
        """
        if client_data and not self.client_id:
            # Créer le client associé avec is_company=False
            client = Client.objects.create(
                name=client_data['name'],
                address=client_data['address'],
                phone=client_data['phone'],
                email=client_data['email'],
                website_url=client_data['website_url'],
                is_company=False
            )
            self.client = client
        
        super().save(*args, **kwargs)
