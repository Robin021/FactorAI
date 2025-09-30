"""
Configuration service for managing system and user configurations
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from models.config import (
    Config,
    ConfigInDB,
    ConfigType,
    LLMConfig,
    DataSourceConfig,
    SystemConfig,
    UserPreferenceConfig,
    LLMProvider,
    DataSourceType
)
from core.database import get_database, Depends

# Import TradingAgents config components for compatibility
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.config.config_manager import ConfigManager

# Import logging
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('config_service')


class ConfigService:
    """Service for managing configurations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.config_manager = ConfigManager()
    
    async def get_user_config(
        self,
        user_id: str,
        config_type: ConfigType
    ) -> Optional[Config]:
        """
        Get a specific user configuration
        """
        config_doc = await self.db.configs.find_one({
            "user_id": ObjectId(user_id),
            "config_type": config_type.value
        })
        
        if config_doc:
            config_db = ConfigInDB(**config_doc)
            return self._convert_to_config_response(config_db)
        
        # Return default configuration if not found
        default_config = self._get_default_config(config_type)
        if default_config:
            return Config(
                id="default",
                user_id=user_id,
                config_type=config_type,
                config_data=default_config,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        
        return None
    
    async def get_user_configs(
        self,
        user_id: str,
        config_type: Optional[ConfigType] = None
    ) -> List[Config]:
        """
        Get all user configurations or by type
        """
        query_filter = {"user_id": ObjectId(user_id)}
        if config_type:
            query_filter["config_type"] = config_type.value
        
        cursor = self.db.configs.find(query_filter)
        configs = []
        
        async for config_doc in cursor:
            config_db = ConfigInDB(**config_doc)
            configs.append(self._convert_to_config_response(config_db))
        
        return configs
    
    async def update_user_config(
        self,
        user_id: str,
        config_type: ConfigType,
        config_data: Dict[str, Any]
    ) -> Config:
        """
        Update or create user configuration
        """
        # Validate configuration data
        self._validate_config_data(config_type, config_data)
        
        # Check if configuration exists
        existing_config = await self.db.configs.find_one({
            "user_id": ObjectId(user_id),
            "config_type": config_type.value
        })
        
        if existing_config:
            # Update existing configuration
            await self.db.configs.update_one(
                {"_id": existing_config["_id"]},
                {
                    "$set": {
                        "config_data": config_data,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            updated_doc = await self.db.configs.find_one({"_id": existing_config["_id"]})
            config_db = ConfigInDB(**updated_doc)
        else:
            # Create new configuration
            config_db = ConfigInDB(
                user_id=ObjectId(user_id),
                config_type=config_type,
                config_data=config_data
            )
            
            result = await self.db.configs.insert_one(config_db.dict(by_alias=True))
            config_db.id = result.inserted_id
        
        # Update TradingAgents config if needed
        await self._sync_with_trading_agents_config(user_id, config_type, config_data)
        
        return self._convert_to_config_response(config_db)
    
    async def update_data_source_configs(
        self,
        user_id: str,
        data_sources: List[DataSourceConfig]
    ) -> List[Config]:
        """
        Update multiple data source configurations
        """
        # Delete existing data source configs
        await self.db.configs.delete_many({
            "user_id": ObjectId(user_id),
            "config_type": ConfigType.DATA_SOURCE.value
        })
        
        configs = []
        for ds_config in data_sources:
            config = await self.update_user_config(
                user_id=user_id,
                config_type=ConfigType.DATA_SOURCE,
                config_data=ds_config.dict()
            )
            configs.append(config)
        
        return configs
    
    async def get_system_config(self) -> Config:
        """
        Get system configuration
        """
        config_doc = await self.db.configs.find_one({
            "user_id": None,
            "config_type": ConfigType.SYSTEM.value
        })
        
        if config_doc:
            config_db = ConfigInDB(**config_doc)
            return self._convert_to_config_response(config_db)
        
        # Return default system configuration
        default_config = self._get_default_config(ConfigType.SYSTEM)
        return Config(
            id="system_default",
            user_id=None,
            config_type=ConfigType.SYSTEM,
            config_data=default_config,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    async def update_system_config(self, config_data: Dict[str, Any]) -> Config:
        """
        Update system configuration
        """
        # Validate configuration data
        self._validate_config_data(ConfigType.SYSTEM, config_data)
        
        # Check if system configuration exists
        existing_config = await self.db.configs.find_one({
            "user_id": None,
            "config_type": ConfigType.SYSTEM.value
        })
        
        if existing_config:
            # Update existing configuration
            await self.db.configs.update_one(
                {"_id": existing_config["_id"]},
                {
                    "$set": {
                        "config_data": config_data,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            updated_doc = await self.db.configs.find_one({"_id": existing_config["_id"]})
            config_db = ConfigInDB(**updated_doc)
        else:
            # Create new system configuration
            config_db = ConfigInDB(
                user_id=None,
                config_type=ConfigType.SYSTEM,
                config_data=config_data
            )
            
            result = await self.db.configs.insert_one(config_db.dict(by_alias=True))
            config_db.id = result.inserted_id
        
        return self._convert_to_config_response(config_db)
    
    async def delete_user_config(
        self,
        user_id: str,
        config_type: ConfigType
    ) -> bool:
        """
        Delete user configuration
        """
        result = await self.db.configs.delete_one({
            "user_id": ObjectId(user_id),
            "config_type": config_type.value
        })
        
        return result.deleted_count > 0
    
    async def reset_user_configs(self, user_id: str) -> int:
        """
        Reset all user configurations to defaults
        """
        # Delete all user configurations
        result = await self.db.configs.delete_many({"user_id": ObjectId(user_id)})
        
        # Create default configurations
        default_configs = [
            (ConfigType.LLM, self._get_default_config(ConfigType.LLM)),
            (ConfigType.DATA_SOURCE, self._get_default_config(ConfigType.DATA_SOURCE)),
            (ConfigType.USER_PREFERENCE, self._get_default_config(ConfigType.USER_PREFERENCE))
        ]
        
        created_count = 0
        for config_type, config_data in default_configs:
            if config_data:
                await self.update_user_config(user_id, config_type, config_data)
                created_count += 1
        
        return created_count
    
    async def export_user_configs(self, user_id: str) -> Dict[str, Any]:
        """
        Export all user configurations
        """
        configs = await self.get_user_configs(user_id)
        
        export_data = {}
        for config in configs:
            export_data[config.config_type.value] = config.config_data
        
        return export_data
    
    async def import_user_configs(
        self,
        user_id: str,
        config_data: Dict[str, Any]
    ) -> int:
        """
        Import user configurations
        """
        imported_count = 0
        
        for config_type_str, data in config_data.get("configs", {}).items():
            try:
                config_type = ConfigType(config_type_str)
                await self.update_user_config(user_id, config_type, data)
                imported_count += 1
            except ValueError:
                logger.warning(f"Unknown config type: {config_type_str}")
                continue
            except Exception as e:
                logger.error(f"Failed to import config {config_type_str}: {str(e)}")
                continue
        
        return imported_count
    
    async def test_llm_connection(self, llm_config: LLMConfig) -> Dict[str, Any]:
        """
        Test LLM configuration connectivity
        """
        try:
            # Create a test LLM instance based on provider
            if llm_config.provider == LLMProvider.OPENAI:
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(
                    model=llm_config.model_name,
                    api_key=llm_config.api_key,
                    base_url=llm_config.api_base,
                    temperature=llm_config.temperature,
                    max_tokens=llm_config.max_tokens,
                    timeout=llm_config.timeout
                )
            elif llm_config.provider == LLMProvider.DASHSCOPE:
                from tradingagents.llm_adapters import ChatDashScope
                llm = ChatDashScope(
                    model=llm_config.model_name,
                    dashscope_api_key=llm_config.api_key,
                    temperature=llm_config.temperature,
                    max_tokens=llm_config.max_tokens
                )
            elif llm_config.provider == LLMProvider.DEEPSEEK:
                from tradingagents.llm_adapters import ChatOpenAI
                llm = ChatOpenAI(
                    model=llm_config.model_name,
                    api_key=llm_config.api_key,
                    base_url=llm_config.api_base or "https://api.deepseek.com",
                    temperature=llm_config.temperature,
                    max_tokens=llm_config.max_tokens
                )
            elif llm_config.provider == LLMProvider.GEMINI:
                from langchain_google_genai import ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(
                    model=llm_config.model_name,
                    google_api_key=llm_config.api_key,
                    temperature=llm_config.temperature,
                    max_tokens=llm_config.max_tokens
                )
            else:
                raise ValueError(f"Unsupported LLM provider: {llm_config.provider}")
            
            # Test with a simple message
            test_message = "Hello, this is a connection test."
            response = await asyncio.wait_for(
                llm.ainvoke(test_message),
                timeout=llm_config.timeout
            )
            
            return {
                "provider": llm_config.provider.value,
                "model": llm_config.model_name,
                "response_length": len(str(response.content)) if hasattr(response, 'content') else 0,
                "test_successful": True
            }
            
        except Exception as e:
            raise Exception(f"LLM connection test failed: {str(e)}")
    
    async def test_data_source_connection(
        self,
        ds_config: DataSourceConfig
    ) -> Dict[str, Any]:
        """
        Test data source configuration connectivity
        """
        try:
            if ds_config.source_type == DataSourceType.TUSHARE:
                import tushare as ts
                ts.set_token(ds_config.api_key)
                pro = ts.pro_api()
                # Test with a simple query
                df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name')
                return {
                    "source": "tushare",
                    "records_count": len(df),
                    "test_successful": True
                }
            
            elif ds_config.source_type == DataSourceType.AKSHARE:
                import akshare as ak
                # Test with a simple query
                df = ak.stock_zh_a_spot_em()
                return {
                    "source": "akshare",
                    "records_count": len(df),
                    "test_successful": True
                }
            
            elif ds_config.source_type == DataSourceType.FINNHUB:
                import finnhub
                finnhub_client = finnhub.Client(api_key=ds_config.api_key)
                # Test with a simple query
                quote = finnhub_client.quote('AAPL')
                return {
                    "source": "finnhub",
                    "test_data": quote,
                    "test_successful": True
                }
            
            elif ds_config.source_type == DataSourceType.BAOSTOCK:
                import baostock as bs
                lg = bs.login()
                if lg.error_code != '0':
                    raise Exception(f"BaoStock login failed: {lg.error_msg}")
                
                # Test with a simple query
                rs = bs.query_stock_basic()
                bs.logout()
                
                return {
                    "source": "baostock",
                    "login_successful": True,
                    "test_successful": True
                }
            
            else:
                raise ValueError(f"Unsupported data source: {ds_config.source_type}")
                
        except Exception as e:
            raise Exception(f"Data source connection test failed: {str(e)}")
    
    def _validate_config_data(self, config_type: ConfigType, config_data: Dict[str, Any]):
        """
        Validate configuration data based on type
        """
        if config_type == ConfigType.LLM:
            LLMConfig(**config_data)  # This will raise ValidationError if invalid
        elif config_type == ConfigType.DATA_SOURCE:
            DataSourceConfig(**config_data)
        elif config_type == ConfigType.SYSTEM:
            SystemConfig(**config_data)
        elif config_type == ConfigType.USER_PREFERENCE:
            UserPreferenceConfig(**config_data)
    
    def _get_default_config(self, config_type: ConfigType) -> Dict[str, Any]:
        """
        Get default configuration for a given type
        """
        if config_type == ConfigType.LLM:
            return {
                "provider": "openai",
                "model_name": "gpt-3.5-turbo",
                "api_key": "",
                "api_base": None,
                "temperature": 0.7,
                "max_tokens": None,
                "timeout": 30,
                "retry_attempts": 3,
                "enabled": True
            }
        elif config_type == ConfigType.DATA_SOURCE:
            return {
                "source_type": "akshare",
                "api_key": None,
                "api_secret": None,
                "base_url": None,
                "priority": 1,
                "timeout": 30,
                "cache_ttl": 3600,
                "enabled": True
            }
        elif config_type == ConfigType.SYSTEM:
            return {
                "max_concurrent_analyses": 5,
                "default_analysis_timeout": 1800,
                "cache_enabled": True,
                "log_level": "INFO",
                "maintenance_mode": False
            }
        elif config_type == ConfigType.USER_PREFERENCE:
            return {
                "default_market_type": "cn",
                "preferred_analysts": ["market", "news", "fundamentals"],
                "notification_enabled": True,
                "theme": "light",
                "language": "zh-CN"
            }
        
        return {}
    
    async def _sync_with_trading_agents_config(
        self,
        user_id: str,
        config_type: ConfigType,
        config_data: Dict[str, Any]
    ):
        """
        Sync configuration with TradingAgents config system
        """
        try:
            if config_type == ConfigType.LLM:
                # Update TradingAgents LLM configuration
                self.config_manager.update_llm_config(config_data)
            elif config_type == ConfigType.DATA_SOURCE:
                # Update TradingAgents data source configuration
                self.config_manager.update_data_source_config(config_data)
        except Exception as e:
            logger.warning(f"Failed to sync with TradingAgents config: {str(e)}")
    
    def _convert_to_config_response(self, config_db: ConfigInDB) -> Config:
        """
        Convert database config model to API response model
        """
        return Config(
            id=str(config_db.id),
            user_id=str(config_db.user_id) if config_db.user_id else None,
            config_type=config_db.config_type,
            config_data=config_db.config_data,
            created_at=config_db.created_at,
            updated_at=config_db.updated_at
        )


# Dependency function
async def get_config_service(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> ConfigService:
    """
    Dependency to get config service instance
    """
    return ConfigService(db)