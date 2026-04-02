"""
Schémas Pydantic pour validation et documentation API
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
# Request Bodies
# ══════════════════════════════════════════════════════════════════════════════

class SetupSaveBody(BaseModel):
    """Configuration des services externes - Toutes les clés sont chiffrées en AES-256-GCM"""
    jellyfinUrl: str = Field(..., description="URL du serveur Jellyfin (requis)", min_length=1, 
                            pattern=r'^https?://')
    jellyfinApiKey: str = Field(default="", description="Clé API Jellyfin (optionnelle pour test)")
    jellyseerrUrl: str = Field(default="", description="URL Jellyseerr (optionnelle)")
    jellyseerrApiKey: str = Field(default="", description="Clé API Jellyseerr")
    radarrUrl: str = Field(default="", description="URL Radarr (optionnelle)")
    radarrApiKey: str = Field(default="", description="Clé API Radarr")
    sonarrUrl: str = Field(default="", description="URL Sonarr (optionnelle)")
    sonarrApiKey: str = Field(default="", description="Clé API Sonarr")
    
    class Config:
        json_schema_extra = {
            "example": {
                "jellyfinUrl": "https://jellyfin.example.com",
                "jellyfinApiKey": "your-api-key-here",
                "jellyseerrUrl": "https://jellyseerr.example.com",
                "jellyseerrApiKey": "jellyseerr-api-key"
            }
        }

class SetupTestBody(BaseModel):
    type: str = Field(..., description="Type de service à tester")
    url: str = Field(..., description="URL du service")
    apiKey: str = Field(default="", description="Clé API")

class LoginBody(BaseModel):
    """Authentification Jellyfin"""
    username: str = Field(..., description="Nom d'utilisateur Jellyfin", min_length=1, max_length=100)
    password: str = Field(default="", description="Mot de passe Jellyfin (peut être vide)", max_length=256)
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "test",
                "password": ""
            }
        }

class PreferencesSaveBody(BaseModel):
    favoriteGenres: Optional[List[str]] = Field(default=[], description="Genres favoris")
    dislikedGenres: Optional[List[str]] = Field(default=[], description="Genres détestés")
    preferredType: Optional[str] = Field(default='', description="Type préféré: movie/tv/both")
    onboardingComplete: Optional[bool] = Field(default=False, description="Onboarding terminé")

class RatingBody(BaseModel):
    """Corps de requête pour noter un média"""
    itemId: str = Field(..., description="ID Jellyfin de l'item à noter", min_length=1)
    value: int = Field(..., ge=0, le=5, description="Note de 0 à 5 étoiles")
    genres: List[str] = Field(default=[], description="Genres du média (pour améliorer DagzRank)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "itemId": "abc123",
                "value": 5,
                "genres": ["Action", "Thriller"]
            }
        }

class MediaRequestBody(BaseModel):
    mediaType: str = Field(..., description="Type: movie ou tv")
    tmdbId: str = Field(..., description="ID TMDB du média")
    provider: str = Field(default="auto", description="Provider: jellyseerr/radarr/sonarr/auto")

class ProgressReportBody(BaseModel):
    itemId: str = Field(..., description="ID de l'item")
    positionTicks: int = Field(..., description="Position en ticks (100ns)")
    isPaused: bool = Field(default=False, description="En pause")
    isStopped: bool = Field(default=False, description="Arrêté")
    playSessionId: Optional[str] = Field(default=None, description="ID de session de lecture")
    mediaSourceId: Optional[str] = Field(default=None, description="ID de la source média")

# ══════════════════════════════════════════════════════════════════════════════
# Response Models
# ══════════════════════════════════════════════════════════════════════════════

class UserResponse(BaseModel):
    id: str
    name: str
    role: str

class LoginResponse(BaseModel):
    success: bool
    user: Optional[UserResponse] = None
    onboardingComplete: bool = False
    error: Optional[str] = None

class SetupCheckResponse(BaseModel):
    setupComplete: bool

class GenreResponse(BaseModel):
    id: str
    name: str

class GenresListResponse(BaseModel):
    genres: List[GenreResponse]

class MediaItemResponse(BaseModel):
    id: str
    name: str
    type: str
    year: Optional[int] = None
    overview: Optional[str] = None
    posterUrl: Optional[str] = None
    backdropUrl: Optional[str] = None
    genres: List[str] = []
    communityRating: Optional[float] = None
    runtime: Optional[int] = None
    mediaStatus: Optional[int] = None
    isFavorite: bool = False

class MediaListResponse(BaseModel):
    items: List[MediaItemResponse]
    totalRecordCount: int = 0

class StreamInfoResponse(BaseModel):
    playMode: str = Field(..., description="direct ou hls")
    streamUrl: str
    languageMode: str
    selectedAudioIndex: int
    selectedSubtitleIndex: int
    audioTracks: List[dict] = []
    subtitleTracks: List[dict] = []
    subtitleVttUrl: Optional[str] = None
    itemId: str
    playSessionId: str
    mediaSourceId: str

class SuccessResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None

class PreferencesResponse(BaseModel):
    favoriteGenres: List[str] = []
    dislikedGenres: List[str] = []
    preferredType: str = ''
    onboardingComplete: bool = False
