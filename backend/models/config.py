"""
Configuration data models
"""
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
from bson import ObjectId

from .user import PyObjectId


class ConfigType(str, Enum):
    """Configuration type enumeration"""
    LLM = "llm"
    DATA_SOURCE = "data_source"
    SYSTEM = "system"
    USER_PREFERENCE = "user_preference"


class LLMProvider(str, Enum):
    """LLM provider enumeration"""
    OPENAI = "openai"
    DASHSCOPE = "dashscope"
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"
    QIANFAN = "qianfan"


class DataSourceType(str, Enum):
    """Data source type enumeration"""
    TUSHARE = "tushare"
    AKSHARE = "akshare"
    FINNHUB = "finnhub"
    BAOSTOCK = "baostock"


class LLMConfig(BaseModel):
    """LLM configuration model"""
    provider: LLMProvider
    model_name: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    timeout: int = Field(default=30, ge=1)
    retry_attempts: int = Field(default=3, ge=1)
    enabled: bool = True


class DataSourceConfig(BaseModel):
    """Data source configuration model"""
    source_type: DataSourceType
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    base_url: Optional[str] = None
    priority: int = Field(default=1, ge=1)
    timeout: int = Field(default=30, ge=1)
    cache_ttl: int = Field(default=3600, ge=0)  # seconds
    enabled: bool = True


class SystemConfig(BaseModel):
    """System configuration model"""
    max_concurrent_analyses: int = Field(default=5, ge=1)
    default_analysis_timeout: int = Field(default=1800, ge=60)  # seconds
    cache_enabled: bool = True
    log_level: str = Field(default="INFO")
    maintenance_mode: bool = False


class UserPreferenceConfig(BaseModel):
    """User preference configuration model"""
    default_market_type: str = "cn"
    preferred_analysts: list = Field(default_factory=list)
    notification_enabled: bool = True
    theme: str = "light"
    language: str = "zh-CN"


class ConfigInDB(BaseModel):
    """Configuration model as stored in database"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: Optional[PyObjectId] = None  # None for system-wide configs
    config_type: ConfigType
    config_data: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Config(BaseModel):
    """Configuration model for API responses"""
    id: str
    user_id: Optional[str] = None
    config_type: ConfigType
    config_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConfigUpdate(BaseModel):
    """Configuration update model"""
    config_data: Dict[str, Any]


class ConfigListResponse(BaseModel):
    """Configuration list response model"""
    configs: list[Config]
    total: int