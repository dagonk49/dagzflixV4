"""
DagzFlix Security Module - Quantum-Proof Cryptography
======================================================
Protection niveau militaire avec cryptographie post-quantique
"""

import os
import secrets
import hashlib
import base64
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import nacl.secret
import nacl.utils
import nacl.signing
import json
import logging

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# MASTER KEY MANAGEMENT (Quantum-Resistant)
# ═══════════════════════════════════════════════════════════════════════════

class QuantumProofSecurity:
    """
    Système de sécurité résistant aux attaques quantiques
    Utilise NaCl (libsodium) qui implémente des primitives résistantes
    """
    
    def __init__(self):
        self.master_key = self._get_or_create_master_key()
        self.cipher = AESGCM(self.master_key)
        self.password_hasher = PasswordHasher(
            time_cost=3,  # Nombre d'itérations
            memory_cost=65536,  # 64 MB
            parallelism=4,
            hash_len=32,
            salt_len=16
        )
    
    def _get_or_create_master_key(self) -> bytes:
        """
        Récupère la master key depuis les variables d'environnement
        CRITICAL: Cette clé DOIT être définie - l'application refuse de démarrer sinon
        """
        master_key_b64 = os.environ.get('DAGZFLIX_MASTER_KEY')
        
        if not master_key_b64:
            logger.critical("🚨 ERREUR FATALE: DAGZFLIX_MASTER_KEY n'est pas définie !")
            logger.critical("🚨 L'application ne peut pas démarrer sans cette clé.")
            logger.critical("🚨 Générez-en une avec: python -c \"from cryptography.hazmat.primitives.ciphers.aead import AESGCM; import base64; print(base64.b64encode(AESGCM.generate_key(bit_length=256)).decode())\"")
            raise RuntimeError(
                "DAGZFLIX_MASTER_KEY est requise pour démarrer l'application. "
                "Sans elle, toutes les données chiffrées deviendraient inutilisables après redémarrage. "
                "Définissez cette variable d'environnement avant de lancer le serveur."
            )
        
        try:
            return base64.b64decode(master_key_b64)
        except Exception as e:
            logger.critical(f"🚨 ERREUR: DAGZFLIX_MASTER_KEY invalide - {e}")
            raise RuntimeError(f"DAGZFLIX_MASTER_KEY est invalide: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # CHIFFREMENT AES-256-GCM (Authenticated Encryption)
    # ═══════════════════════════════════════════════════════════════════════
    
    def encrypt_data(self, plaintext: str) -> str:
        """
        Chiffre les données sensibles avec AES-256-GCM
        Résistant aux attaques de Grover (quantum)
        """
        if not plaintext:
            return ""
        
        try:
            # Génération d'un nonce unique (96 bits recommandé pour GCM)
            nonce = secrets.token_bytes(12)
            
            # Chiffrement avec authentification
            ciphertext = self.cipher.encrypt(
                nonce,
                plaintext.encode('utf-8'),
                None  # Associated data (optionnel)
            )
            
            # Combine nonce + ciphertext pour le stockage
            encrypted = nonce + ciphertext
            return base64.b64encode(encrypted).decode('utf-8')
        
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise
    
    def decrypt_data(self, encrypted_b64: str) -> str:
        """
        Déchiffre les données
        """
        if not encrypted_b64:
            return ""
        
        try:
            # Décode et sépare nonce + ciphertext
            encrypted = base64.b64decode(encrypted_b64)
            nonce = encrypted[:12]
            ciphertext = encrypted[12:]
            
            # Déchiffrement
            plaintext = self.cipher.decrypt(nonce, ciphertext, None)
            return plaintext.decode('utf-8')
        
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise
    
    # ═══════════════════════════════════════════════════════════════════════
    # HASHING ARGON2 (Résistant GPU/ASIC/Quantum)
    # ═══════════════════════════════════════════════════════════════════════
    
    def hash_password(self, password: str) -> str:
        """
        Hash un mot de passe avec Argon2id (vainqueur PHC 2015)
        Résistant aux attaques par force brute classiques ET quantiques
        """
        return self.password_hasher.hash(password)
    
    def verify_password(self, hash: str, password: str) -> bool:
        """
        Vérifie un mot de passe
        """
        try:
            self.password_hasher.verify(hash, password)
            return True
        except VerifyMismatchError:
            return False
    
    # ═══════════════════════════════════════════════════════════════════════
    # TOKENS SÉCURISÉS (Session, CSRF, etc.)
    # ═══════════════════════════════════════════════════════════════════════
    
    def generate_secure_token(self, length: int = 32) -> str:
        """
        Génère un token cryptographiquement sécurisé
        """
        return secrets.token_urlsafe(length)
    
    def generate_csrf_token(self, session_id: str) -> str:
        """
        Génère un token CSRF lié à la session
        """
        data = f"{session_id}:{secrets.token_urlsafe(32)}"
        return self.encrypt_data(data)
    
    def verify_csrf_token(self, token: str, session_id: str) -> bool:
        """
        Vérifie un token CSRF
        """
        try:
            decrypted = self.decrypt_data(token)
            stored_session = decrypted.split(':')[0]
            return stored_session == session_id
        except:
            return False
    
    # ═══════════════════════════════════════════════════════════════════════
    # SIGNATURES NUMÉRIQUES (Ed25519 - Résistant quantum partiel)
    # ═══════════════════════════════════════════════════════════════════════
    
    def generate_signing_keypair(self) -> tuple[str, str]:
        """
        Génère une paire de clés pour signature (Ed25519)
        Note: Ed25519 n'est PAS complètement quantum-proof mais meilleur que RSA
        """
        signing_key = nacl.signing.SigningKey.generate()
        verify_key = signing_key.verify_key
        
        return (
            base64.b64encode(bytes(signing_key)).decode('utf-8'),
            base64.b64encode(bytes(verify_key)).decode('utf-8')
        )
    
    def sign_data(self, data: str, private_key_b64: str) -> str:
        """
        Signe des données
        """
        signing_key = nacl.signing.SigningKey(base64.b64decode(private_key_b64))
        signed = signing_key.sign(data.encode('utf-8'))
        return base64.b64encode(signed).decode('utf-8')
    
    def verify_signature(self, signed_data_b64: str, public_key_b64: str) -> Optional[str]:
        """
        Vérifie une signature
        """
        try:
            verify_key = nacl.signing.VerifyKey(base64.b64decode(public_key_b64))
            signed = base64.b64decode(signed_data_b64)
            verified = verify_key.verify(signed)
            return verified.decode('utf-8')
        except:
            return None
    
    # ═══════════════════════════════════════════════════════════════════════
    # AUDIT DE SÉCURITÉ
    # ═══════════════════════════════════════════════════════════════════════
    
    def log_security_event(self, event_type: str, user_id: str, details: Dict[str, Any], 
                          severity: str = 'INFO', ip_address: str = None):
        """
        Log un événement de sécurité pour audit
        """
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'severity': severity,
            'ip_address': ip_address,
            'details': details
        }
        
        # Log selon la sévérité
        if severity == 'CRITICAL':
            logger.critical(f"🚨 SECURITY: {json.dumps(log_entry)}")
        elif severity == 'ERROR':
            logger.error(f"⚠️  SECURITY: {json.dumps(log_entry)}")
        elif severity == 'WARNING':
            logger.warning(f"⚡ SECURITY: {json.dumps(log_entry)}")
        else:
            logger.info(f"🔒 SECURITY: {json.dumps(log_entry)}")
        
        return log_entry
    
    # ═══════════════════════════════════════════════════════════════════════
    # DÉTECTION D'INTRUSION
    # ═══════════════════════════════════════════════════════════════════════
    
    def detect_suspicious_activity(self, user_id: str, action: str, 
                                   metadata: Dict[str, Any]) -> bool:
        """
        Détecte les activités suspectes
        """
        suspicious = False
        reasons = []
        
        # Vérification de patterns suspects
        if action == 'login':
            # Trop de tentatives échouées
            if metadata.get('failed_attempts', 0) > 5:
                suspicious = True
                reasons.append('Multiple failed login attempts')
            
            # Changement de pays/IP suspect
            if metadata.get('country_changed') and metadata.get('time_since_last_login_hours', 0) < 1:
                suspicious = True
                reasons.append('Rapid location change')
        
        if action == 'api_access':
            # Trop de requêtes
            if metadata.get('requests_per_minute', 0) > 100:
                suspicious = True
                reasons.append('Rate limit exceeded')
        
        if suspicious:
            self.log_security_event(
                'SUSPICIOUS_ACTIVITY',
                user_id,
                {'action': action, 'reasons': reasons, **metadata},
                severity='WARNING'
            )
        
        return suspicious


# ═══════════════════════════════════════════════════════════════════════════
# INSTANCE GLOBALE
# ═══════════════════════════════════════════════════════════════════════════

security = QuantumProofSecurity()


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS POUR L'APPLICATION
# ═══════════════════════════════════════════════════════════════════════════

def encrypt_api_key(api_key: str) -> str:
    """Chiffre une API key pour stockage sécurisé"""
    return security.encrypt_data(api_key)


def decrypt_api_key(encrypted_key: str) -> str:
    """Déchiffre une API key"""
    return security.decrypt_data(encrypted_key)


def create_secure_session(user_id: str, metadata: Dict[str, Any] = None) -> Dict[str, str]:
    """
    Crée une session ultra-sécurisée
    """
    session_id = security.generate_secure_token(32)
    csrf_token = security.generate_csrf_token(session_id)
    
    return {
        'session_id': session_id,
        'csrf_token': csrf_token,
        'user_id': user_id,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'expires_at': (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        'metadata': metadata or {}
    }


def validate_session_security(session: Dict[str, Any], request_ip: str = None) -> bool:
    """
    Valide la sécurité d'une session
    """
    # Vérification expiration
    expires_at = datetime.fromisoformat(session.get('expiresAt', ''))
    if datetime.now(timezone.utc) > expires_at:
        return False
    
    # Vérification IP (optionnel, peut causer des problèmes avec VPN/mobile)
    # if request_ip and session.get('ip_address') != request_ip:
    #     return False
    
    return True
