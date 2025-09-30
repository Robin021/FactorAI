"""
Application configuration management
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "TradingAgents API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Modern web API for stock analysis platform"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database Configuration
    MONGODB_URL: str
    MONGODB_DB_NAME: str = "tradingagents"
    REDIS_URL: str
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # AI API Keys (Optional)
    DASHSCOPE_API_KEY: Optional[str] = None
    FINNHUB_API_KEY: Optional[str] = None
    TUSHARE_TOKEN: Optional[str] = None
    SILICONFLOW_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: Optional[str] = None
    YOUR_PROVIDER_API_KEY: Optional[str] = None
    YOUR_PROVIDER_BASE_URL: Optional[str] = None
    QIANFAN_API_KEY: Optional[str] = None
    CUSTOM_OPENAI_API_KEY: Optional[str] = None
    
    # Feature Flags
    TUSHARE_ENABLED: bool = False
    DEEPSEEK_ENABLED: bool = False
    MONGODB_ENABLED: bool = False
    REDIS_ENABLED: bool = False
    MEMORY_ENABLED: bool = True
    ENABLE_COST_TRACKING: bool = True
    USE_MONGODB_STORAGE: bool = False
    
    # Data Sources
    DEFAULT_CHINA_DATA_SOURCE: str = "akshare"
    
    # Directories
    TRADINGAGENTS_RESULTS_DIR: str = "./results"
    TRADINGAGENTS_DATA_DIR: str = "./data"
    TRADINGAGENTS_CACHE_DIR: str = "./cache"
    TRADINGAGENTS_LOG_LEVEL: str = "INFO"
    
    # Database Details
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_USERNAME: Optional[str] = None
    MONGODB_PASSWORD: Optional[str] = None
    MONGODB_DATABASE: str = "tradingagents"
    MONGODB_AUTH_SOURCE: str = "admin"
    MONGODB_CONNECTION_STRING: Optional[str] = None
    DATABASE_NAME: str = "tradingagents"
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    # Cost Tracking
    COST_ALERT_THRESHOLD: float = 100.0
    MAX_USAGE_RECORDS: int = 10000
    
    # Reddit API (Optional)
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    REDDIT_USER_AGENT: str = "TradingAgents-CN/1.0"
    
    # Authing SSO (Optional)
    AUTHING_APP_ID: Optional[str] = None
    AUTHING_APP_HOST: Optional[str] = None
    AUTHING_REDIRECT_URI: Optional[str] = None
    AUTHING_APP_SECRET: Optional[str] = None
    
    # System Configuration
    PYTHONDONTWRITEBYTECODE: Optional[str] = None
    MAX_WORKERS: Optional[int] = None
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略额外的环境变量


# Global settings instance
settings = Settings()