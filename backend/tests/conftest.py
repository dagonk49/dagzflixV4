"""
Configuration pytest pour les tests
"""
import pytest
import os

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Setup global pour tous les tests
    Définit les variables d'environnement nécessaires
    """
    # Master key de test (NE PAS utiliser en production)
    os.environ['DAGZFLIX_MASTER_KEY'] = 'dGVzdF9rZXlfMTIzNDU2Nzg5MGFiY2RlZjEyMzQ1Njc4OTA='
    os.environ['MONGO_URL'] = 'mongodb://localhost:27017'
    os.environ['DB_NAME'] = 'dagzflix_test'
    
    yield
    
    # Cleanup si nécessaire
    pass
