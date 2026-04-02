"""
Tests pour le module de sécurité
"""
import pytest
from security import QuantumProofSecurity
import os

class TestQuantumProofSecurity:
    """Tests du module de sécurité quantum-proof"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        # Définir une master key de test
        os.environ['DAGZFLIX_MASTER_KEY'] = 'dGVzdF9rZXlfMTIzNDU2Nzg5MGFiY2RlZjEyMzQ1Njc4OTA='
        self.security = QuantumProofSecurity()
    
    def test_master_key_required(self):
        """Test que l'application refuse de démarrer sans MASTER_KEY"""
        # Sauvegarder la clé actuelle
        original_key = os.environ.get('DAGZFLIX_MASTER_KEY')
        
        # Retirer la clé
        if 'DAGZFLIX_MASTER_KEY' in os.environ:
            del os.environ['DAGZFLIX_MASTER_KEY']
        
        # Doit lever une RuntimeError
        with pytest.raises(RuntimeError, match="DAGZFLIX_MASTER_KEY"):
            QuantumProofSecurity()
        
        # Restaurer la clé
        if original_key:
            os.environ['DAGZFLIX_MASTER_KEY'] = original_key
    
    def test_encrypt_decrypt_data(self):
        """Test chiffrement/déchiffrement AES-256-GCM"""
        plaintext = "sensitive-api-key-12345"
        
        # Chiffrement
        encrypted = self.security.encrypt_data(plaintext)
        assert encrypted != plaintext
        assert len(encrypted) > 0
        
        # Déchiffrement
        decrypted = self.security.decrypt_data(encrypted)
        assert decrypted == plaintext
    
    def test_encrypt_empty_string(self):
        """Test chiffrement d'une chaîne vide"""
        encrypted = self.security.encrypt_data("")
        assert encrypted == ""
        
        decrypted = self.security.decrypt_data("")
        assert decrypted == ""
    
    def test_hash_password_argon2(self):
        """Test hashing de mot de passe avec Argon2id"""
        password = "SuperSecretPassword123!"
        
        # Hash
        hashed = self.security.hash_password(password)
        assert hashed != password
        assert hashed.startswith('$argon2')  # Format Argon2
        
        # Vérification correcte
        assert self.security.verify_password(hashed, password) is True
        
        # Vérification incorrecte
        assert self.security.verify_password(hashed, "WrongPassword") is False
    
    def test_generate_secure_token(self):
        """Test génération de tokens sécurisés"""
        token1 = self.security.generate_secure_token(32)
        token2 = self.security.generate_secure_token(32)
        
        # Doit être unique
        assert token1 != token2
        
        # Longueur approximative (URL-safe base64)
        assert len(token1) > 30
    
    def test_csrf_token_generation(self):
        """Test génération et vérification de tokens CSRF"""
        session_id = "test-session-123"
        
        # Génération
        csrf_token = self.security.generate_csrf_token(session_id)
        assert len(csrf_token) > 0
        
        # Vérification correcte
        assert self.security.verify_csrf_token(csrf_token, session_id) is True
        
        # Vérification avec mauvaise session
        assert self.security.verify_csrf_token(csrf_token, "wrong-session") is False
    
    def test_security_event_logging(self):
        """Test logging des événements de sécurité"""
        event = self.security.log_security_event(
            'LOGIN_SUCCESS',
            'user123',
            {'ip': '1.2.3.4'},
            severity='INFO',
            ip_address='1.2.3.4'
        )
        
        assert event['event_type'] == 'LOGIN_SUCCESS'
        assert event['user_id'] == 'user123'
        assert event['severity'] == 'INFO'
        assert 'timestamp' in event

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
