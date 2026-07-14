from django.db.models.functions import Now

from django.db import models

class HelpDocument(models.Model):
    LEVEL_CHOICES = [
        ('admin', 'Admin'),
        ('commercial', 'Commercial'),
    ]
    
    TYPE_CHOICES = [
        ('navigation', 'Navigation'),
        ('url', 'URL'),
        ('erreur', 'Erreur'),
    ]

    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    title = models.CharField(max_length=255)
    step = models.CharField(null=True, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    content = models.TextField()
    updated_at = models.DateTimeField(db_default=Now())

    def __str__(self):
        return f"[{self.level.upper()}] {self.title}"

    class Meta:
        db_table = 'help_document'