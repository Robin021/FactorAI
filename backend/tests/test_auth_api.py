"""
Tests for authentication API endpoints
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

from ..models.user import UserRole
from ..core.auth import create_access_token, get_password_hash


class TestAuthLogin:
    """Test login endpoint"""
    
    def test_login_success(self, test_client, test_user):
        """Test successful login"""
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        
        response = test_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_login_invalid_username(self, test_client):
        """Test login with invalid username"""
        login_data = {
            "username": "nonexistent",
            "password": "testpassword123"
        }
        
        response = test_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]
    
    def test_login_invalid_password(self, test_client, test_user):
        """Test login with invalid password"""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        response = test_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_inactive_user(self, test_client, test_db):
        """Test login with inactive user"""
        # Create inactive user
        from ..models.user import UserInDB
        
        inactive_user = UserInDB(
            username="inactive",
            email="inactive@example.com",
            role=UserRole.USER,
            permissions=[],
            password_hash=get_password_hash("password123"),
            is_active=False,
            created_at=datetime.utcnow()
        )
        
        await test_db.users.insert_one(inactive_user.dict(by_alias=True))
        
        login_data = {
            "username": "inactive",
            "password": "password123"
        }
        
        response = test_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "User account is disabled" in response.json()["detail"]


class TestAuthLogout:
    """Test logout endpoints"""
    
    def test_logout_success(self, test_client, auth_headers):
        """Test successful logout"""
        response = test_client.post("/api/v1/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"
    
    def test_logout_without_auth(self, test_client):
        """Test logout without authentication"""
        response = test_client.post("/api/v1/auth/logout")
        
        assert response.status_code == 401
    
    def test_logout_all_success(self, test_client, auth_headers):
        """Test logout from all devices"""
        response = test_client.post("/api/v1/auth/logout-all", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out from all devices"


class TestUserInfo:
    """Test user information endpoints"""
    
    def test_get_current_user(self, test_client, auth_headers):
        """Test getting current user info"""
        response = test_client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["role"] == "user"
        assert "password_hash" not in data  # Should not expose password hash
    
    def test_get_current_user_without_auth(self, test_client):
        """Test getting current user without authentication"""
        response = test_client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    def test_update_current_user(self, test_client, auth_headers):
        """Test updating current user info"""
        update_data = {
            "username": "updateduser",
            "email": "updated@example.com"
        }
        
        response = test_client.put("/api/v1/auth/me", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updateduser"
        assert data["email"] == "updated@example.com"
    
    @pytest.mark.asyncio
    async def test_update_user_duplicate_username(self, test_client, auth_headers, test_db):
        """Test updating user with duplicate username"""
        # Create another user
        from ..models.user import UserInDB
        
        other_user = UserInDB(
            username="otheruser",
            email="other@example.com",
            role=UserRole.USER,
            permissions=[],
            password_hash=get_password_hash("password123"),
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        await test_db.users.insert_one(other_user.dict(by_alias=True))
        
        update_data = {
            "username": "otheruser"
        }
        
        response = test_client.put("/api/v1/auth/me", json=update_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]


class TestTokenRefresh:
    """Test token refresh endpoint"""
    
    def test_refresh_token_success(self, test_client, auth_headers):
        """Test successful token refresh"""
        response = test_client.post("/api/v1/auth/refresh", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_refresh_token_without_auth(self, test_client):
        """Test token refresh without authentication"""
        response = test_client.post("/api/v1/auth/refresh")
        
        assert response.status_code == 401


class TestPasswordChange:
    """Test password change endpoint"""
    
    def test_change_password_success(self, test_client, auth_headers):
        """Test successful password change"""
        password_data = {
            "old_password": "testpassword123",
            "new_password": "newpassword123"
        }
        
        response = test_client.post("/api/v1/auth/change-password", json=password_data, headers=auth_headers)
        
        assert response.status_code == 200
        assert "Password changed successfully" in response.json()["message"]
    
    def test_change_password_wrong_old_password(self, test_client, auth_headers):
        """Test password change with wrong old password"""
        password_data = {
            "old_password": "wrongpassword",
            "new_password": "newpassword123"
        }
        
        response = test_client.post("/api/v1/auth/change-password", json=password_data, headers=auth_headers)
        
        assert response.status_code == 401
        assert "Invalid current password" in response.json()["detail"]
    
    def test_change_password_weak_new_password(self, test_client, auth_headers):
        """Test password change with weak new password"""
        password_data = {
            "old_password": "testpassword123",
            "new_password": "weak"
        }
        
        response = test_client.post("/api/v1/auth/change-password", json=password_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "Password must be at least 8 characters long" in response.json()["detail"]


class TestUserManagement:
    """Test user management endpoints (admin only)"""
    
    def test_create_user_success(self, test_client, admin_headers):
        """Test successful user creation"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "role": "user",
            "permissions": ["analysis.read"],
            "is_active": True
        }
        
        response = test_client.post("/api/v1/auth/users", json=user_data, headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "user"
        assert "password" not in data  # Should not expose password
    
    def test_create_user_duplicate_username(self, test_client, admin_headers, test_user):
        """Test creating user with duplicate username"""
        user_data = {
            "username": "testuser",  # Already exists
            "email": "different@example.com",
            "password": "password123",
            "role": "user"
        }
        
        response = test_client.post("/api/v1/auth/users", json=user_data, headers=admin_headers)
        
        assert response.status_code == 400
        assert "Username already exists" in response.json()["detail"]
    
    def test_create_user_non_admin(self, test_client, auth_headers):
        """Test creating user as non-admin"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "role": "user"
        }
        
        response = test_client.post("/api/v1/auth/users", json=user_data, headers=auth_headers)
        
        assert response.status_code == 403
    
    def test_list_users_success(self, test_client, admin_headers):
        """Test listing users"""
        response = test_client.get("/api/v1/auth/users", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least the admin user
    
    def test_get_user_success(self, test_client, admin_headers, test_user):
        """Test getting specific user"""
        user_id = str(test_user.id)
        response = test_client.get(f"/api/v1/auth/users/{user_id}", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
    
    def test_get_user_not_found(self, test_client, admin_headers):
        """Test getting non-existent user"""
        from bson import ObjectId
        fake_id = str(ObjectId())
        
        response = test_client.get(f"/api/v1/auth/users/{fake_id}", headers=admin_headers)
        
        assert response.status_code == 404
    
    def test_update_user_success(self, test_client, admin_headers, test_user):
        """Test updating user"""
        user_id = str(test_user.id)
        update_data = {
            "username": "updatedtestuser",
            "role": "viewer"
        }
        
        response = test_client.put(f"/api/v1/auth/users/{user_id}", json=update_data, headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updatedtestuser"
        assert data["role"] == "viewer"
    
    def test_delete_user_success(self, test_client, admin_headers, test_user):
        """Test deleting user"""
        user_id = str(test_user.id)
        
        response = test_client.delete(f"/api/v1/auth/users/{user_id}", headers=admin_headers)
        
        assert response.status_code == 200
        assert "User deleted successfully" in response.json()["message"]
    
    def test_delete_self_forbidden(self, test_client, admin_headers, test_admin):
        """Test that admin cannot delete themselves"""
        admin_id = str(test_admin.id)
        
        response = test_client.delete(f"/api/v1/auth/users/{admin_id}", headers=admin_headers)
        
        assert response.status_code == 400
        assert "Cannot delete your own account" in response.json()["detail"]


class TestPasswordReset:
    """Test password reset endpoints"""
    
    def test_request_password_reset_success(self, test_client, test_user):
        """Test successful password reset request"""
        reset_data = {
            "email": "test@example.com"
        }
        
        response = test_client.post("/api/v1/auth/request-password-reset", json=reset_data)
        
        assert response.status_code == 200
        assert "password reset link has been sent" in response.json()["message"]
    
    def test_request_password_reset_nonexistent_email(self, test_client):
        """Test password reset request with non-existent email"""
        reset_data = {
            "email": "nonexistent@example.com"
        }
        
        response = test_client.post("/api/v1/auth/request-password-reset", json=reset_data)
        
        # Should still return success to prevent email enumeration
        assert response.status_code == 200
        assert "password reset link has been sent" in response.json()["message"]
    
    @patch('backend.core.auth.create_access_token')
    def test_reset_password_success(self, mock_create_token, test_client, mock_redis, test_user):
        """Test successful password reset"""
        # Mock token creation
        reset_token = "mock_reset_token"
        mock_create_token.return_value = reset_token
        
        # Mock Redis to return user ID for the token
        mock_redis.get.return_value = str(test_user.id).encode()
        
        reset_data = {
            "token": reset_token,
            "new_password": "newpassword123"
        }
        
        with patch('jose.jwt.decode') as mock_decode:
            mock_decode.return_value = {
                "sub": str(test_user.id),
                "type": "password_reset"
            }
            
            response = test_client.post("/api/v1/auth/reset-password", json=reset_data)
        
        assert response.status_code == 200
        assert "Password reset successfully" in response.json()["message"]
    
    def test_reset_password_invalid_token(self, test_client):
        """Test password reset with invalid token"""
        reset_data = {
            "token": "invalid_token",
            "new_password": "newpassword123"
        }
        
        response = test_client.post("/api/v1/auth/reset-password", json=reset_data)
        
        assert response.status_code == 400
        assert "Invalid reset token" in response.json()["detail"]


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_login_rate_limiting(self, test_client, mock_redis):
        """Test login rate limiting"""
        # Mock Redis to simulate rate limit exceeded
        mock_redis.get.return_value = b'10'  # Max requests reached
        
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        
        response = test_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]