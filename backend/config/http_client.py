"""
Client HTTP avec Connection Pooling
Performance: Réutilisation des connexions TCP/TLS
"""
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Client HTTP global (initialisé au démarrage)
http_client: httpx.AsyncClient = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestion du cycle de vie de l'application
    - Startup: Initialise le client HTTP avec connection pooling
    - Shutdown: Ferme proprement le client HTTP
    """
    global http_client
    
    # Startup
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, connect=10.0),
        limits=httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20,
            keepalive_expiry=30.0
        ),
        follow_redirects=True,
        http2=True  # HTTP/2 pour meilleures performances
    )
    
    print("✅ HTTP Client initialized with connection pooling")
    
    yield
    
    # Shutdown
    await http_client.aclose()
    print("✅ HTTP Client closed")

def get_http_client() -> httpx.AsyncClient:
    """Retourne le client HTTP global"""
    if http_client is None:
        raise RuntimeError("HTTP client not initialized")
    return http_client
