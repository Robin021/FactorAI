"""
Configuration management API endpoints
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from models.user import UserInDB
from models.config import (
    Config,
    ConfigInDB,
    ConfigType,
    ConfigUpdate,
    ConfigListResponse,
    LLMConfig,
    DataSourceConfig,
    SystemConfig,
    UserPreferenceConfig,
    LLMProvider,
    DataSourceType
)
from core.security import (
    get_current_active_user,
    require_permissions,
    get_current_admin_user,
    Permissions
)
from core.database import get_database
from services.config_service import ConfigService, get_config_service

router = APIRouter()


@router.get("/llm", response_model=Config)
async def get_llm_config(
    current_user: UserInDB = Depends(require_permissions([Permissions.CONFIG_READ])),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Get LLM configuration for current user
    """
    config = await config_service.get_user_config(
        user_id=str(current_user.id),
        config_type=ConfigType.LLM
    )
    return config


@router.put("/llm", response_model=Config)
async def update_llm_config(
    config_update: ConfigUpdate,
    current_user: UserInDB = Depends(require_permissions([Permissions.CONFIG_UPDATE])),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Update LLM configuration for current user
    """
    # Validate LLM configuration
    llm_config = LLMConfig(**config_update.config_data)
    _validate_llm_config(llm_config)
    
    config = await config_service.update_user_config(
        user_id=str(current_user.id),
        config_type=ConfigType.LLM,
        config_data=config_update.config_data
    )
    return config


@router.get("/llm/providers")
async def get_llm_providers(
    current_user: UserInDB = Depends(require_permissions([Permissions.CONFIG_READ]))
):
    """
    Get available LLM providers and their models
    """
    providers = {
        LLMProvider.OPENAI: {
            "name": "OpenAI",
            "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            "requires_api_key": True,
            "api_base_configurable": True
        },
        LLMProvider.DASHSCOPE: {
            "name": "阿里百炼 (DashScope)",
            "models": ["qwen-turbo", "qwen-plus", "qwen-max"],
            "requires_api_key": True,
            "api_base_configurable": False
        },
        LLMProvider.DEEPSEEK: {
            "name": "DeepSeek",
            "models": ["deepseek-chat", "deepseek-coder"],
            "requires_api_key": True,
            "api_base_configurable": True
        },
        LLMProvider.GEMINI: {
            "name": "Google Gemini",
            "models": ["gemini-pro", "gemini-2.0-flash"],
            "requires_api_key": True,
            "api_base_configurable": False
        },
        LLMProvider.QIANFAN: {
            "name": "百度千帆",
            "models": ["ernie-bot", "ernie-bot-turbo"],
            "requires_api_key": True,
            "api_base_configurable": False
        }
    }
    return providers


@router.get("/default-model")
async def get_default_model_config():
    """
    Get default model configuration with available models
    (Public endpoint - no authentication required)
    """
    import os
    from tradingagents.default_config import DEFAULT_CONFIG
    
    # Get available models based on configured API keys
    available_models = []
    
    # Check DashScope (阿里百炼)
    if os.getenv("DASHSCOPE_API_KEY"):
        for model in ["qwen-turbo", "qwen-plus", "qwen-max"]:
            available_models.append({
                "provider": "dashscope",
                "model_name": model,
                "enabled": True,
                "max_tokens": 2000,
                "temperature": 0.7
            })
    
    # Check DeepSeek
    if os.getenv("DEEPSEEK_API_KEY") and os.getenv("DEEPSEEK_ENABLED", "false").lower() == "true":
        for model in ["deepseek-chat", "deepseek-coder"]:
            available_models.append({
                "provider": "deepseek",
                "model_name": model,
                "enabled": True,
                "max_tokens": 4000,
                "temperature": 0.7
            })
    
    # Check OpenAI
    if os.getenv("OPENAI_API_KEY"):
        for model in ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o-mini"]:
            available_models.append({
                "provider": "openai",
                "model_name": model,
                "enabled": True,
                "max_tokens": 4000,
                "temperature": 0.7
            })
    
    # Check OpenRouter
    if os.getenv("OPENROUTER_API_KEY"):
        for model in ["anthropic/claude-3.5-sonnet", "google/gemini-2.0-flash-exp:free"]:
            available_models.append({
                "provider": "openai",  # OpenRouter uses OpenAI-compatible API
                "model_name": model,
                "enabled": True,
                "max_tokens": 4000,
                "temperature": 0.7
            })
    
    # Check Google Gemini
    if os.getenv("GOOGLE_API_KEY"):
        for model in ["gemini-pro", "gemini-2.0-flash"]:
            available_models.append({
                "provider": "google",
                "model_name": model,
                "enabled": True,
                "max_tokens": 2048,
                "temperature": 0.7
            })
    
    # Check Qianfan (百度千帆)
    if os.getenv("QIANFAN_API_KEY"):
        for model in ["ernie-bot", "ernie-bot-turbo"]:
            available_models.append({
                "provider": "qianfan",
                "model_name": model,
                "enabled": True,
                "max_tokens": 2000,
                "temperature": 0.7
            })
    
    # Get current default from DEFAULT_CONFIG
    default_provider = DEFAULT_CONFIG.get("llm_provider", "openai")
    default_model = DEFAULT_CONFIG.get("deep_think_llm", "gpt-4o-mini")
    
    return {
        "default_provider": default_provider,
        "default_model": default_model,
        "available_models": available_models
    }


@router.put("/default-model")
async def update_default_model_config(
    request_data: Dict[str, Any],
    current_user: UserInDB = Depends(require_permissions([Permissions.CONFIG_UPDATE])),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Update default model configuration
    """
    provider = request_data.get("provider")
    model_name = request_data.get("model_name")
    
    if not provider or not model_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider and model_name are required"
        )
    
    # Update DEFAULT_CONFIG
    from tradingagents.default_config import DEFAULT_CONFIG
    DEFAULT_CONFIG["llm_provider"] = provider
    DEFAULT_CONFIG["deep_think_llm"] = model_name
    DEFAULT_CONFIG["quick_think_llm"] = model_name
    
    return {
        "success": True,
        "message": "Default model updated successfully",
        "provider": provider,
        "model_name": model_name
    }


@router.post("/llm/test")
async def test_llm_config(
    llm_config: LLMConfig,
    current_user: UserInDB = Depends(require_permissions([Permissions.CONFIG_UPDATE])),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Test LLM configuration connectivity
    """
    try:
        result = await config_service.test_llm_connection(llm_config)
        return {"success": True, "message": "LLM connection successful", "details": result}
    except Exception as e:
        return {"success": False, "message": f"LLM connection failed: {str(e)}"}


@router.get("/data-sources", response_model=List[Config])
async def get_data_source_configs(
    current_user: UserInDB = Depends(require_permissions([Permissions.CONFIG_READ])),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Get data source configurations for current user
    """
    configs = await config_service.get_user_configs(
        user_id=str(current_user.id),
        config_type=ConfigType.DATA_SOURCE
    )
    return configs


@router.put("/data-sources", response_model=List[Config])
async def update_data_source_configs(
    request_data: Dict[str, Any],
    current_user: UserInDB = Depends(require_permissions([Permissions.CONFIG_UPDATE])),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Update data source configurations for current user
    """
    # Extract configs from request
    data_sources = [DataSourceConfig(**config) for config in request_data.get("configs", [])]
    
    # Validate data source configurations
    for ds_config in data_sources:
        _validate_data_source_config(ds_config)
    
    configs = await config_service.update_data_source_configs(
        user_id=str(current_user.id),
        data_sources=data_sources
    )
    return configs


@router.get("/data-sources/types")
async def get_data_source_types(
    current_user: UserInDB = Depends(require_permissions([Permissions.CONFIG_READ]))
):
    """
    Get available data source types and their requirements
    """
    data_sources = {
        DataSourceType.TUSHARE: {
            "name": "Tushare",
            "description": "专业的股票数据接口",
            "markets": ["cn"],
            "requires_api_key": True,
            "free_tier": True,
            "features": ["股价数据", "财务数据", "基本面数据"]
        },
        DataSourceType.AKSHARE: {
            "name": "AKShare",
            "description": "开源财经数据接口库",
            "markets": ["cn", "us", "hk"],
            "requires_api_key": False,
            "free_tier": True,
            "features": ["股价数据", "新闻数据", "宏观数据"]
        },
        DataSourceType.FINNHUB: {
            "name": "Finnhub",
            "description": "全球股票数据API",
            "markets": ["us", "hk"],
            "requires_api_key": True,
            "free_tier": True,
            "features": ["股价数据", "新闻数据", "财务数据"]
        },
        DataSourceType.BAOSTOCK: {
            "name": "BaoStock",
            "description": "免费开源的证券数据平台",
            "markets": ["cn"],
            "requires_api_key": False,
            "free_tier": True,
            "features": ["股价数据", "财务数据"]
        }
    }
    return data_sources


@router.post("/data-sources/test")
async def test_data_source_config(
    data_source_config: DataSourceConfig,
    current_user: UserInDB = Depends(require_permissions([Permissions.CONFIG_UPDATE])),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Test data source configuration connectivity
    """
    try:
        result = await config_service.test_data_source_connection(data_source_config)
        return {"success": True, "message": "Data source connection successful", "details": result}
    except Exception as e:
        return {"success": False, "message": f"Data source connection failed: {str(e)}"}


@router.get("/system", response_model=Config)
async def get_system_config(
    current_user: UserInDB = Depends(get_current_admin_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Get system configuration (admin only)
    """
    config = await config_service.get_system_config()
    return config


@router.put("/system", response_model=Config)
async def update_system_config(
    config_update: ConfigUpdate,
    current_user: UserInDB = Depends(get_current_admin_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Update system configuration (admin only)
    """
    # Validate system configuration
    system_config = SystemConfig(**config_update.config_data)
    _validate_system_config(system_config)
    
    config = await config_service.update_system_config(config_update.config_data)
    return config


@router.get("/preferences", response_model=Config)
async def get_user_preferences(
    current_user: UserInDB = Depends(get_current_active_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Get user preferences
    """
    config = await config_service.get_user_config(
        user_id=str(current_user.id),
        config_type=ConfigType.USER_PREFERENCE
    )
    return config


@router.put("/preferences", response_model=Config)
async def update_user_preferences(
    config_update: ConfigUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Update user preferences
    """
    # Validate user preferences
    preferences = UserPreferenceConfig(**config_update.config_data)
    
    config = await config_service.update_user_config(
        user_id=str(current_user.id),
        config_type=ConfigType.USER_PREFERENCE,
        config_data=config_update.config_data
    )
    return config


@router.get("/export")
async def export_user_configs(
    current_user: UserInDB = Depends(require_permissions([Permissions.CONFIG_READ])),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Export user configurations
    """
    configs = await config_service.export_user_configs(str(current_user.id))
    return {
        "user_id": str(current_user.id),
        "username": current_user.username,
        "exported_at": datetime.utcnow().isoformat(),
        "configs": configs
    }


@router.post("/import")
async def import_user_configs(
    config_data: Dict[str, Any],
    current_user: UserInDB = Depends(require_permissions([Permissions.CONFIG_UPDATE])),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Import user configurations
    """
    try:
        imported_count = await config_service.import_user_configs(
            user_id=str(current_user.id),
            config_data=config_data
        )
        return {
            "success": True,
            "message": f"Successfully imported {imported_count} configurations",
            "imported_count": imported_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to import configurations: {str(e)}"
        )


@router.delete("/{config_type}")
async def delete_user_config(
    config_type: ConfigType,
    current_user: UserInDB = Depends(require_permissions([Permissions.CONFIG_UPDATE])),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Delete user configuration by type
    """
    deleted = await config_service.delete_user_config(
        user_id=str(current_user.id),
        config_type=config_type
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No {config_type.value} configuration found"
        )
    
    return {"message": f"{config_type.value} configuration deleted successfully"}


@router.post("/reset")
async def reset_user_configs(
    current_user: UserInDB = Depends(require_permissions([Permissions.CONFIG_UPDATE])),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Reset all user configurations to defaults
    """
    reset_count = await config_service.reset_user_configs(str(current_user.id))
    return {
        "message": f"Successfully reset {reset_count} configurations to defaults",
        "reset_count": reset_count
    }


def _validate_llm_config(llm_config: LLMConfig):
    """
    Validate LLM configuration
    """
    if llm_config.provider in [LLMProvider.OPENAI, LLMProvider.DASHSCOPE, LLMProvider.DEEPSEEK]:
        if not llm_config.api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{llm_config.provider.value} requires an API key"
            )
    
    if llm_config.temperature < 0 or llm_config.temperature > 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Temperature must be between 0 and 2"
        )
    
    if llm_config.max_tokens is not None and llm_config.max_tokens < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Max tokens must be greater than 0"
        )


def _validate_data_source_config(ds_config: DataSourceConfig):
    """
    Validate data source configuration
    """
    if ds_config.source_type == DataSourceType.TUSHARE:
        if not ds_config.api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tushare requires an API key"
            )
    
    if ds_config.source_type == DataSourceType.FINNHUB:
        if not ds_config.api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Finnhub requires an API key"
            )
    
    if ds_config.priority < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Priority must be greater than 0"
        )


def _validate_system_config(system_config: SystemConfig):
    """
    Validate system configuration
    """
    if system_config.max_concurrent_analyses < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Max concurrent analyses must be greater than 0"
        )
    
    if system_config.default_analysis_timeout < 60:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Default analysis timeout must be at least 60 seconds"
        )
    
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if system_config.log_level not in valid_log_levels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Log level must be one of: {', '.join(valid_log_levels)}"
        )