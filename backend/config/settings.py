"""
Configuration centralisée de l'application
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
ROOT_DIR = Path(__file__).parent.parent.parent
load_dotenv(ROOT_DIR / 'backend' / '.env')

class Settings:
    """Configuration de l'application"""
    
    # MongoDB
    MONGO_URL: str = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    DB_NAME: str = os.environ.get('DB_NAME', 'dagzflix')
    
    # Sécurité
    DAGZFLIX_MASTER_KEY: str = os.environ.get('DAGZFLIX_MASTER_KEY', '')
    CORS_ORIGINS: list = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # API Keys (seront déchiffrées depuis la DB)
    # Ces valeurs ne sont jamais hardcodées
    
    # Application
    APP_NAME: str = "DagzFlix API"
    VERSION: str = "1.0.0"
    
    # Rate Limiting
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_SETUP: str = "5/minute"
    RATE_LIMIT_DEFAULT: str = "100/minute"
    
    # Session
    SESSION_MAX_AGE: int = 7 * 24 * 3600  # 7 jours
    
    @classmethod
    def validate(cls):
        """Valide que toutes les variables critiques sont présentes"""
        if not cls.DAGZFLIX_MASTER_KEY:
            raise RuntimeError(
                "DAGZFLIX_MASTER_KEY est requise. "
                "Définissez cette variable d'environnement avant de lancer le serveur."
            )

settings = Settings()
