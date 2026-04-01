# 🛡️ DagzFlix Security Documentation

## 🔐 Niveau de Sécurité : **MILITAIRE / QUANTUM-PROOF**

DagzFlix implémente une sécurité de niveau bancaire avec résistance aux attaques quantiques.

---

## 📋 Table des Matières
1. [Chiffrement](#chiffrement)
2. [Protection Quantum](#protection-quantum)
3. [Authentification](#authentification)
4. [Protection des Sessions](#protection-des-sessions)
5. [Rate Limiting](#rate-limiting)
6. [Headers de Sécurité](#headers-de-sécurité)
7. [Audit & Logs](#audit--logs)
8. [Configuration Production](#configuration-production)

---

## 🔒 Chiffrement

### AES-256-GCM (Authenticated Encryption)
- **Algorithme** : AES-256-GCM
- **Résistance Quantum** : ✅ (sécurité post-quantique avec clés 256-bit)
- **Usage** :
  - API Keys (Jellyfin, Radarr, Sonarr, Jellyseerr)
  - Tokens de session Jellyfin
  - Données sensibles utilisateur

### Caractéristiques
- ✅ Authentification intégrée (détecte les modifications)
- ✅ Nonce unique par chiffrement (96-bit)
- ✅ Protection contre replay attacks
- ✅ AEAD (Authenticated Encryption with Associated Data)

**Stockage** :
```
nonce (12 bytes) + ciphertext (variable) → base64
```

---

## ⚛️ Protection Quantum

### Algorithmes Résistants
1. **AES-256-GCM** : Résiste à l'algorithme de Grover (quantum)
2. **Argon2id** : Memory-hard, résiste aux attaques GPU/ASIC/Quantum
3. **Ed25519** : Partiellement résistant (meilleur que RSA)
4. **NaCl/libsodium** : Primitives modernes cryptographiques

### Pourquoi Quantum-Proof ?
- Les ordinateurs quantiques peuvent casser RSA-2048 en quelques heures
- AES-256 nécessite 2^128 opérations quantiques (encore infaisable)
- Argon2 résiste aux optimisations quantiques (memory-bound)

---

## 👤 Authentification

### Argon2id Password Hashing
```python
Paramètres :
- time_cost: 3 itérations
- memory_cost: 64 MB
- parallelism: 4 threads  
- hash_len: 32 bytes
- salt_len: 16 bytes
```

### Caractéristiques
- ✅ Vainqueur Password Hashing Competition 2015
- ✅ Résiste aux attaques GPU (memory-hard)
- ✅ Résiste aux attaques ASIC  
- ✅ Résiste aux attaques quantiques (memory-bound)
- ✅ Auto-salting unique par mot de passe

---

## 🔑 Protection des Sessions

### Sécurité Cookies
```python
HttpOnly: True     # Bloque accès JavaScript (XSS)
Secure: True       # HTTPS uniquement
SameSite: Strict   # Bloque CSRF
Max-Age: 7 jours   # Expiration automatique
```

### Session Token
- **Génération** : `secrets.token_urlsafe(32)` (256-bit entropie)
- **Stockage** : MongoDB avec index TTL
- **Expiration** : Automatique après 7 jours
- **Validation** : IP tracking (optionnel), User-Agent, CSRF token

### CSRF Protection
- Token chiffré lié à la session
- Validation sur toutes les requêtes POST/PUT/DELETE
- Régénération à chaque login

---

## 🚦 Rate Limiting

### Limites par Endpoint

| Endpoint | Limite | Fenêtre |
|----------|--------|---------|
| `/auth/login` | 5 requêtes | 1 minute |
| `/setup/save` | 5 requêtes | 1 minute |
| API Standard | 100 requêtes | 1 minute |

### Protection DDoS
- Rate limiting par IP
- Automatic 429 response
- Logs des abus

---

## 🛡️ Headers de Sécurité

### Headers Implémentés
```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
Content-Security-Policy: [strict policy]
```

### Content Security Policy (CSP)
- Script sources limitées
- Inline scripts contrôlés (React nécessite unsafe-eval)
- Fonts: Google Fonts uniquement
- Images: Self + HTTPS
- Frame-ancestors: DENY (pas d'iframe)

---

## 📊 Audit & Logs

### Événements Tracés

#### Sécurité Critique (CRITICAL)
- Tentatives d'intrusion détectées
- Accès non autorisés répétés
- Modifications de sécurité

#### Sécurité Importante (WARNING)
- Échecs de login multiples (>5)
- Changements de géolocalisation rapides
- Rate limit dépassé

#### Information (INFO)
- Login réussi
- Configuration sauvegardée
- Session créée/détruite

### Format de Log
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "event_type": "LOGIN_FAILED",
  "user_id": "user123",
  "severity": "WARNING",
  "ip_address": "1.2.3.4",
  "details": {
    "reason": "Invalid credentials",
    "attempt_count": 3
  }
}
```

---

## ⚙️ Configuration Production

### Variables d'Environnement Requises

```bash
# CRITICAL: Master Key pour chiffrement
DAGZFLIX_MASTER_KEY=<base64_256bit_key>

# MongoDB
MONGO_URL=mongodb://...

# CORS (strictement limité en prod)
CORS_ORIGINS=https://votredomaine.com

# Backend URL
REACT_APP_BACKEND_URL=https://api.votredomaine.com
```

### Génération Master Key
```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64

master_key = AESGCM.generate_key(bit_length=256)
print(base64.b64encode(master_key).decode('utf-8'))
```

⚠️ **CRITIQUE** : Sauvegardez cette clé de manière ultra-sécurisée !
- ❌ Ne JAMAIS commit dans Git
- ✅ Stockage sécurisé (Vault, AWS Secrets Manager, etc.)
- ✅ Backup hors-ligne chiffré
- ✅ Rotation annuelle recommandée

---

## 🔍 Détection d'Intrusion

### Patterns Suspects Détectés

1. **Brute Force Login**
   - >5 tentatives échouées
   - Action: Rate limit + log WARNING

2. **Géolocalisation Impossible**
   - Changement de pays en <1h
   - Action: log WARNING + 2FA (future)

3. **API Abuse**
   - >100 requêtes/minute
   - Action: Rate limit 429 + log WARNING

4. **Session Hijacking**
   - IP change during session
   - Action: Optional logout (configurable)

---

## 📈 Checklist Déploiement

### Avant Production

- [ ] Générer et sauvegarder DAGZFLIX_MASTER_KEY
- [ ] Configurer CORS_ORIGINS strict (pas de wildcard)
- [ ] Activer HTTPS uniquement (Let's Encrypt)
- [ ] Configurer backup MongoDB chiffré
- [ ] Tester rate limiting
- [ ] Vérifier tous les logs de sécurité
- [ ] Scanner vulnérabilités (OWASP ZAP)
- [ ] Audit de pénétration recommandé

### Monitoring

- [ ] Alertes sur événements CRITICAL
- [ ] Dashboard logs sécurité
- [ ] Métriques rate limiting
- [ ] Rapport hebdomadaire tentatives intrusion

---

## 🏆 Certifications Visées

- ✅ OWASP Top 10 Compliance
- ✅ PCI-DSS Ready (si paiements futurs)
- ✅ RGPD Compliant (chiffrement données personnelles)
- ✅ ISO 27001 Ready

---

## 📞 Support Sécurité

En cas de faille de sécurité détectée :
1. Ne PAS divulguer publiquement
2. Contacter immédiatement l'équipe
3. Fournir reproduction steps
4. Patch en <24h garanti

---

## 🎓 Références

- [NIST Post-Quantum Cryptography](https://csrc.nist.gov/projects/post-quantum-cryptography)
- [Argon2 RFC 9106](https://datatracker.ietf.org/doc/html/rfc9106)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [NaCl Cryptography](https://nacl.cr.yp.to/)

---

**Version** : 1.0.0  
**Dernière mise à jour** : 2024  
**Niveau de sécurité** : 🔥 QUANTUM-PROOF 🔥
