"""
Tests for configuration API endpoints
"""
import pytest
from unittest.mock import patch, AsyncMock

from ..models.config import ConfigType, LLMProvider, DataSourceType


class TestLLMConfig:
    """Test LLM configuration endpoints"""
    
    def test_get_llm_configs_success(self, test_client, auth_headers):
        """Test successful LLM config retrieval"""
        response = test_client.get("/api/v1/config/llm", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_llm_config_success(self, test_client, auth_headers):
        """Test successful LLM config update"""
        llm_config = {
            "provider": "openai",
            "model_name": "gpt-3.5-turbo",
            "api_key": "test-api-key",
            "temperature": 0.7,
            "max_tokens": 1000,
            "timeout": 30,
            "retry_attempts": 3,
            "enabled": True
        }
        
        response = test_client.put("/api/v1/config/llm", json=llm_config, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["config_type"] == "llm"
        assert data["config_data"]["provider"] == "openai"
    
    def test_update_llm_config_invalid_temperature(self, test_client, auth_headers):
        """Test LLM config update with invalid temperature"""
        llm_config = {
            "provider": "openai",
            "model_name": "gpt-3.5-turbo",
            "api_key": "test-api-key",
            "temperature": 3.0,  # Invalid: > 2.0
            "enabled": True
        }
        
        response = test_client.put("/api/v1/config/llm", json=llm_config, headers=auth_headers)
        
        assert response.status_code == 400
        assert "Temperature must be between 0 and 2" in response.json()["detail"]
    
    def test_update_llm_config_missing_api_key(self, test_client, auth_headers):
        """Test LLM config update with missing API key for providers that require it"""
        llm_config = {
            "provider": "openai",
            "model_name": "gpt-3.5-turbo",
            # Missing api_key
            "temperature": 0.7,
            "enabled": True
        }
        
        response = test_client.put("/api/v1/config/llm", json=llm_config, headers=auth_headers)
        
        assert response.status_code == 400
        assert "requires an API key" in response.json()["detail"]
    
    def test_get_llm_providers(self, test_client, auth_headers):
        """Test getting available LLM providers"""
        response = test_client.get("/api/v1/config/llm/providers", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "openai" in data
        assert "dashscope" in data
        assert "deepseek" in data
        assert "gemini" in data
        
        # Check provider structure
        openai_info = data["openai"]
        assert "name" in openai_info
        assert "models" in openai_info
        assert "requires_api_key" in openai_info
    
    @patch('backend.services.config_service.ConfigService.test_llm_connection')
    def test_test_llm_config_success(self, mock_test, test_client, auth_headers):
        """Test successful LLM configuration test"""
        mock_test.return_value = {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "response_length": 50,
            "test_successful": True
        }
        
        llm_config = {
            "provider": "openai",
            "model_name": "gpt-3.5-turbo",
            "api_key": "test-api-key",
            "temperature": 0.7,
            "enabled": True
        }
        
        response = test_client.post("/api/v1/config/llm/test", json=llm_config, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "LLM connection successful" in data["message"]
    
    @patch('backend.services.config_service.ConfigService.test_llm_connection')
    def test_test_llm_config_failure(self, mock_test, test_client, auth_headers):
        """Test failed LLM configuration test"""
        mock_test.side_effect = Exception("Invalid API key")
        
        llm_config = {
            "provider": "openai",
            "model_name": "gpt-3.5-turbo",
            "api_key": "invalid-key",
            "temperature": 0.7,
            "enabled": True
        }
        
        response = test_client.post("/api/v1/config/llm/test", json=llm_config, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Invalid API key" in data["message"]


class TestDataSourceConfig:
    """Test data source configuration endpoints"""
    
    def test_get_data_source_configs_success(self, test_client, auth_headers):
        """Test successful data source config retrieval"""
        response = test_client.get("/api/v1/config/data-sources", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_data_source_configs_success(self, test_client, auth_headers):
        """Test successful data source config update"""
        data_sources = [
            {
                "source_type": "akshare",
                "priority": 1,
                "timeout": 30,
                "cache_ttl": 3600,
                "enabled": True
            },
            {
                "source_type": "tushare",
                "api_key": "test-tushare-key",
                "priority": 2,
                "timeout": 30,
                "cache_ttl": 3600,
                "enabled": True
            }
        ]
        
        response = test_client.put("/api/v1/config/data-sources", json=data_sources, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
    
    def test_update_data_source_config_missing_api_key(self, test_client, auth_headers):
        """Test data source config update with missing API key for providers that require it"""
        data_sources = [
            {
                "source_type": "tushare",
                # Missing api_key
                "priority": 1,
                "enabled": True
            }
        ]
        
        response = test_client.put("/api/v1/config/data-sources", json=data_sources, headers=auth_headers)
        
        assert response.status_code == 400
        assert "requires an API key" in response.json()["detail"]
    
    def test_get_data_source_types(self, test_client, auth_headers):
        """Test getting available data source types"""
        response = test_client.get("/api/v1/config/data-sources/types", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "tushare" in data
        assert "akshare" in data
        assert "finnhub" in data
        assert "baostock" in data
        
        # Check data source structure
        tushare_info = data["tushare"]
        assert "name" in tushare_info
        assert "description" in tushare_info
        assert "markets" in tushare_info
        assert "requires_api_key" in tushare_info
    
    @patch('backend.services.config_service.ConfigService.test_data_source_connection')
    def test_test_data_source_config_success(self, mock_test, test_client, auth_headers):
        """Test successful data source configuration test"""
        mock_test.return_value = {
            "source": "akshare",
            "records_count": 1000,
            "test_successful": True
        }
        
        ds_config = {
            "source_type": "akshare",
            "priority": 1,
            "timeout": 30,
            "enabled": True
        }
        
        response = test_client.post("/api/v1/config/data-sources/test", json=ds_config, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Data source connection successful" in data["message"]


class TestSystemConfig:
    """Test system configuration endpoints (admin only)"""
    
    def test_get_system_config_success(self, test_client, admin_headers):
        """Test successful system config retrieval"""
        response = test_client.get("/api/v1/config/system", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["config_type"] == "system"
    
    def test_get_system_config_non_admin(self, test_client, auth_headers):
        """Test system config retrieval as non-admin"""
        response = test_client.get("/api/v1/config/system", headers=auth_headers)
        
        assert response.status_code == 403
    
    def test_update_system_config_success(self, test_client, admin_headers):
        """Test successful system config update"""
        system_config = {
            "max_concurrent_analyses": 10,
            "default_analysis_timeout": 3600,
            "cache_enabled": True,
            "log_level": "DEBUG",
            "maintenance_mode": False
        }
        
        response = test_client.put("/api/v1/config/system", json=system_config, headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["config_type"] == "system"
        assert data["config_data"]["max_concurrent_analyses"] == 10
    
    def test_update_system_config_invalid_values(self, test_client, admin_headers):
        """Test system config update with invalid values"""
        system_config = {
            "max_concurrent_analyses": 0,  # Invalid: must be > 0
            "default_analysis_timeout": 30,  # Invalid: must be >= 60
            "log_level": "INVALID",  # Invalid log level
        }
        
        response = test_client.put("/api/v1/config/system", json=system_config, headers=admin_headers)
        
        assert response.status_code == 400


class TestUserPreferences:
    """Test user preference endpoints"""
    
    def test_get_user_preferences_success(self, test_client, auth_headers):
        """Test successful user preferences retrieval"""
        response = test_client.get("/api/v1/config/user-preferences", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["config_type"] == "user_preference"
    
    def test_update_user_preferences_success(self, test_client, auth_headers):
        """Test successful user preferences update"""
        preferences = {
            "default_market_type": "us",
            "preferred_analysts": ["market", "news"],
            "notification_enabled": False,
            "theme": "dark",
            "language": "en-US"
        }
        
        response = test_client.put("/api/v1/config/user-preferences", json=preferences, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["config_type"] == "user_preference"
        assert data["config_data"]["default_market_type"] == "us"
        assert data["config_data"]["theme"] == "dark"


class TestConfigImportExport:
    """Test configuration import/export endpoints"""
    
    def test_export_user_configs_success(self, test_client, auth_headers):
        """Test successful config export"""
        response = test_client.get("/api/v1/config/export", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "username" in data
        assert "exported_at" in data
        assert "configs" in data
    
    def test_import_user_configs_success(self, test_client, auth_headers):
        """Test successful config import"""
        import_data = {
            "configs": {
                "llm": {
                    "provider": "openai",
                    "model_name": "gpt-4",
                    "api_key": "imported-key",
                    "temperature": 0.5,
                    "enabled": True
                },
                "user_preference": {
                    "default_market_type": "us",
                    "theme": "dark",
                    "language": "en-US"
                }
            }
        }
        
        response = test_client.post("/api/v1/config/import", json=import_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "imported_count" in data
    
    def test_import_user_configs_invalid_data(self, test_client, auth_headers):
        """Test config import with invalid data"""
        import_data = {
            "configs": {
                "invalid_type": {
                    "some": "data"
                }
            }
        }
        
        response = test_client.post("/api/v1/config/import", json=import_data, headers=auth_headers)
        
        # Should still succeed but with 0 imported configs
        assert response.status_code == 200
        data = response.json()
        assert data["imported_count"] == 0


class TestConfigManagement:
    """Test configuration management endpoints"""
    
    def test_delete_user_config_success(self, test_client, auth_headers):
        """Test successful config deletion"""
        # First create a config
        llm_config = {
            "provider": "openai",
            "model_name": "gpt-3.5-turbo",
            "api_key": "test-key",
            "temperature": 0.7,
            "enabled": True
        }
        
        create_response = test_client.put("/api/v1/config/llm", json=llm_config, headers=auth_headers)
        assert create_response.status_code == 200
        
        # Then delete it
        response = test_client.delete("/api/v1/config/llm", headers=auth_headers)
        
        assert response.status_code == 200
        assert "configuration deleted successfully" in response.json()["message"]
    
    def test_delete_nonexistent_config(self, test_client, auth_headers):
        """Test deletion of non-existent config"""
        response = test_client.delete("/api/v1/config/llm", headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_reset_user_configs_success(self, test_client, auth_headers):
        """Test successful config reset"""
        response = test_client.post("/api/v1/config/reset", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "reset_count" in data
        assert "Successfully reset" in data["message"]


class TestConfigPermissions:
    """Test configuration permission requirements"""
    
    def test_config_endpoints_require_auth(self, test_client):
        """Test that config endpoints require authentication"""
        endpoints = [
            ("GET", "/api/v1/config/llm"),
            ("PUT", "/api/v1/config/llm"),
            ("GET", "/api/v1/config/data-sources"),
            ("PUT", "/api/v1/config/data-sources"),
            ("GET", "/api/v1/config/user-preferences"),
            ("PUT", "/api/v1/config/user-preferences"),
        ]
        
        for method, endpoint in endpoints:
            if method == "GET":
                response = test_client.get(endpoint)
            elif method == "PUT":
                response = test_client.put(endpoint, json={})
            
            assert response.status_code == 401
    
    def test_system_config_requires_admin(self, test_client, auth_headers):
        """Test that system config endpoints require admin role"""
        response = test_client.get("/api/v1/config/system", headers=auth_headers)
        assert response.status_code == 403
        
        response = test_client.put("/api/v1/config/system", json={}, headers=auth_headers)
        assert response.status_code == 403