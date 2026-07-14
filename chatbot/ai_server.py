# ai_server.py
from sentence_transformers import SentenceTransformer

class LocalEmbeddingServer:
    _model = None

    @classmethod
    def load_model(cls):
        """Charge le modèle en mémoire RAM au démarrage de Django."""
        if cls._model is None:
            # Modèle ultra-léger (22 Mo), s'exécute en 0.02s sur CPU
            cls._model = SentenceTransformer('all-MiniLM-L6-v2')
            print("=== [IA] Modèle d'embedding sémantique chargé en RAM au démarrage ===")

    @classmethod
    def get_model(cls):
        """Renvoie le modèle prêt à l'emploi."""
        return cls._model