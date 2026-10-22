from django.db import IntegrityError, models


class CompanyType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'company_type'

    @classmethod
    def create_from_name(cls, raw_name):
        """Crée un type d'entreprise ; lève ValueError avec un message affichable si le nom est invalide."""
        name = (raw_name or '').strip()
        if not name:
            raise ValueError("Le nom du type d'entreprise est obligatoire.")
        if len(name) > cls._meta.get_field('name').max_length:
            raise ValueError('Le nom est trop long (50 caractères maximum).')
        if cls.objects.filter(name__iexact=name).exists():
            raise ValueError("Ce type d'entreprise existe déjà.")

        try:
            return cls.objects.create(name=name)
        except IntegrityError:
            raise ValueError("Ce type d'entreprise existe déjà.")
