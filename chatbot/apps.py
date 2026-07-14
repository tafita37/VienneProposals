# apps.py
import sys
from django.apps import AppConfig

class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'

    def ready(self):
        # On vérifie que Django est lancé via le serveur et pas pour une migration ou un test
        if any(cmd in sys.argv for cmd in ['runserver', 'gunicorn', 'uwsgi']):
            # Import local pour éviter les boucles d'import circulaires
            from .ai_server import LocalEmbeddingServer
            
            # Déclenche le chargement unique du modèle en RAM
            LocalEmbeddingServer.load_model()