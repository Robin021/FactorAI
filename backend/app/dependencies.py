"""
FastAPI dependency injection configuration
"""
# Import database dependencies from core module
from ..core.database import get_database, get_redis

# Import authentication dependencies from security module
from ..core.security import (
    get_current_user,
    get_current_active_user,
    get_current_admin_user,
    get_session_manager,
    require_permissions,
    require_roles,
    create_rate_limiter,
    Permissions
)