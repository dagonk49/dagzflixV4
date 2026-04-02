"""
Tests pour les schémas Pydantic
"""
import pytest
from pydantic import ValidationError
from models.schemas import (
    SetupSaveBody, LoginBody, RatingBody, PreferencesSaveBody
)

class TestSchemas:
    """Tests de validation des schémas Pydantic"""
    
    def test_setup_save_body_valid(self):
        """Test validation correcte de SetupSaveBody"""
        data = {
            "jellyfinUrl": "https://jellyfin.example.com",
            "jellyfinApiKey": "test-api-key",
            "jellyseerrUrl": "",
            "jellyseerrApiKey": "",
            "radarrUrl": "",
            "radarrApiKey": "",
            "sonarrUrl": "",
            "sonarrApiKey": ""
        }
        
        schema = SetupSaveBody(**data)
        assert schema.jellyfinUrl == "https://jellyfin.example.com"
        assert schema.jellyfinApiKey == "test-api-key"
    
    def test_setup_save_body_missing_jellyfin_url(self):
        """Test que jellyfinUrl est requis"""
        data = {
            "jellyfinApiKey": "test"
        }
        
        with pytest.raises(ValidationError):
            SetupSaveBody(**data)
    
    def test_setup_save_body_invalid_url(self):
        """Test validation du pattern URL"""
        data = {
            "jellyfinUrl": "not-a-url",
            "jellyfinApiKey": ""
        }
        
        with pytest.raises(ValidationError, match="pattern"):
            SetupSaveBody(**data)
    
    def test_login_body_valid(self):
        """Test validation correcte de LoginBody"""
        data = {
            "username": "test",
            "password": ""
        }
        
        schema = LoginBody(**data)
        assert schema.username == "test"
        assert schema.password == ""
    
    def test_login_body_missing_username(self):
        """Test que username est requis"""
        data = {"password": "test"}
        
        with pytest.raises(ValidationError):
            LoginBody(**data)
    
    def test_rating_body_valid(self):
        """Test validation correcte de RatingBody"""
        data = {
            "itemId": "abc123",
            "value": 5,
            "genres": ["Action", "Thriller"]
        }
        
        schema = RatingBody(**data)
        assert schema.itemId == "abc123"
        assert schema.value == 5
        assert schema.genres == ["Action", "Thriller"]
    
    def test_rating_body_value_constraints(self):
        """Test contraintes sur la note (0-5)"""
        # Valeur trop haute
        with pytest.raises(ValidationError):
            RatingBody(itemId="abc", value=6, genres=[])
        
        # Valeur négative
        with pytest.raises(ValidationError):
            RatingBody(itemId="abc", value=-1, genres=[])
        
        # Valeurs valides
        for value in [0, 1, 2, 3, 4, 5]:
            schema = RatingBody(itemId="abc", value=value, genres=[])
            assert schema.value == value
    
    def test_preferences_save_body_defaults(self):
        """Test valeurs par défaut de PreferencesSaveBody"""
        schema = PreferencesSaveBody()
        
        assert schema.favoriteGenres == []
        assert schema.dislikedGenres == []
        assert schema.preferredType == ''
        assert schema.onboardingComplete is False

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
