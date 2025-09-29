"""
配置文件向后兼容性
支持旧版配置文件格式，提供平滑的配置迁移
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging
from datetime import datetime

from backend.models.config import (
    LLMConfig, DataSourceConfig, SystemConfig, 
    LLMProvider, DataSourceType, ConfigType
)


logger = logging.getLogger(__name__)


class ConfigCompatibilityManager:
    """配置兼容性管理器"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent.parent
        self.legacy_config_paths = [
            self.project_root / "tradingagents" / "default_config.py",
            self.project_root / ".env",
            self.project_root / "config.yaml",
            self.project_root / "config.json"
        ]
    
    def load_legacy_config(self) -> Dict[str, Any]:
        """加载旧版配置文件"""
        merged_config = {}
        
        try:
            # 1. 加载默认配置
            default_config = self._load_default_config()
            if default_config:
                merged_config.update(default_config)
            
            # 2. 加载环境变量配置
            env_config = self._load_env_config()
            if env_config:
                merged_config.update(env_config)
            
            # 3. 加载YAML配置文件
            yaml_config = self._load_yaml_config()
            if yaml_config:
                merged_config.update(yaml_config)
            
            # 4. 加载JSON配置文件
            json_config = self._load_json_config()
            if json_config:
                merged_config.update(json_config)
            
            logger.info(f"成功加载旧版配置，共 {len(merged_config)} 项配置")
            return merged_config
            
        except Exception as e:
            logger.error(f"加载旧版配置失败: {e}")
            return {}
    
    def _load_default_config(self) -> Optional[Dict[str, Any]]:
        """加载默认配置文件"""
        try:
            default_config_path = self.project_root / "tradingagents" / "default_config.py"
            if not default_config_path.exists():
                return None
            
            # 动态导入默认配置
            import sys
            sys.path.insert(0, str(self.project_root))
            
            from tradingagents.default_config import DEFAULT_CONFIG
            
            logger.info("成功加载默认配置文件")
            return DEFAULT_CONFIG
            
        except Exception as e:
            logger.error(f"加载默认配置文件失败: {e}")
            return None
    
    def _load_env_config(self) -> Dict[str, Any]:
        """加载环境变量配置"""
        try:
            env_config = {}
            
            # LLM相关环境变量
            llm_vars = {
                'OPENAI_API_KEY': 'openai_api_key',
                'OPENAI_BASE_URL': 'openai_base_url',
                'OPENAI_MODEL': 'openai_model',
                'DASHSCOPE_API_KEY': 'dashscope_api_key',
                'DEEPSEEK_API_KEY': 'deepseek_api_key',
                'GEMINI_API_KEY': 'gemini_api_key',
                'QIANFAN_API_KEY': 'qianfan_api_key',
                'LLM_PROVIDER': 'llm_provider',
                'LLM_TEMPERATURE': 'llm_temperature',
                'LLM_MAX_TOKENS': 'llm_max_tokens'
            }
            
            for env_var, config_key in llm_vars.items():
                value = os.getenv(env_var)
                if value:
                    env_config[config_key] = value
            
            # 数据源相关环境变量
            data_vars = {
                'TUSHARE_TOKEN': 'tushare_token',
                'FINNHUB_API_KEY': 'finnhub_api_key',
                'ALPHA_VANTAGE_API_KEY': 'alpha_vantage_api_key'
            }
            
            for env_var, config_key in data_vars.items():
                value = os.getenv(env_var)
                if value:
                    env_config[config_key] = value
            
            # 系统相关环境变量
            system_vars = {
                'REDIS_URL': 'redis_url',
                'MONGODB_URL': 'mongodb_url',
                'LOG_LEVEL': 'log_level',
                'DEBUG': 'debug_mode'
            }
            
            for env_var, config_key in system_vars.items():
                value = os.getenv(env_var)
                if value:
                    env_config[config_key] = value
            
            logger.info(f"成功加载环境变量配置，共 {len(env_config)} 项")
            return env_config
            
        except Exception as e:
            logger.error(f"加载环境变量配置失败: {e}")
            return {}
    
    def _load_yaml_config(self) -> Optional[Dict[str, Any]]:
        """加载YAML配置文件"""
        try:
            yaml_path = self.project_root / "config.yaml"
            if not yaml_path.exists():
                return None
            
            with open(yaml_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            logger.info("成功加载YAML配置文件")
            return config
            
        except Exception as e:
            logger.error(f"加载YAML配置文件失败: {e}")
            return None
    
    def _load_json_config(self) -> Optional[Dict[str, Any]]:
        """加载JSON配置文件"""
        try:
            json_path = self.project_root / "config.json"
            if not json_path.exists():
                return None
            
            with open(json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            logger.info("成功加载JSON配置文件")
            return config
            
        except Exception as e:
            logger.error(f"加载JSON配置文件失败: {e}")
            return None
    
    def convert_to_new_format(self, legacy_config: Dict[str, Any]) -> Dict[str, Any]:
        """转换旧版配置到新格式"""
        try:
            new_config = {
                'llm_configs': [],
                'data_source_configs': [],
                'system_config': {},
                'user_preferences': {}
            }
            
            # 转换LLM配置
            llm_config = self._convert_llm_config(legacy_config)
            if llm_config:
                new_config['llm_configs'].append(llm_config)
            
            # 转换数据源配置
            data_source_configs = self._convert_data_source_configs(legacy_config)
            new_config['data_source_configs'].extend(data_source_configs)
            
            # 转换系统配置
            system_config = self._convert_system_config(legacy_config)
            new_config['system_config'] = system_config
            
            # 转换用户偏好
            user_preferences = self._convert_user_preferences(legacy_config)
            new_config['user_preferences'] = user_preferences
            
            logger.info("成功转换配置到新格式")
            return new_config
            
        except Exception as e:
            logger.error(f"转换配置到新格式失败: {e}")
            return {}
    
    def _convert_llm_config(self, legacy_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """转换LLM配置"""
        try:
            # 检测LLM提供商
            provider = legacy_config.get('llm_provider', 'openai').lower()
            
            # 映射提供商名称
            provider_mapping = {
                'openai': LLMProvider.OPENAI,
                'dashscope': LLMProvider.DASHSCOPE,
                'deepseek': LLMProvider.DEEPSEEK,
                'gemini': LLMProvider.GEMINI,
                'qianfan': LLMProvider.QIANFAN
            }
            
            if provider not in provider_mapping:
                provider = LLMProvider.OPENAI
            else:
                provider = provider_mapping[provider]
            
            # 获取API密钥
            api_key = None
            if provider == LLMProvider.OPENAI:
                api_key = legacy_config.get('openai_api_key')
            elif provider == LLMProvider.DASHSCOPE:
                api_key = legacy_config.get('dashscope_api_key')
            elif provider == LLMProvider.DEEPSEEK:
                api_key = legacy_config.get('deepseek_api_key')
            elif provider == LLMProvider.GEMINI:
                api_key = legacy_config.get('gemini_api_key')
            elif provider == LLMProvider.QIANFAN:
                api_key = legacy_config.get('qianfan_api_key')
            
            # 获取模型名称
            model_name = (
                legacy_config.get('openai_model') or
                legacy_config.get('quick_think_llm') or
                legacy_config.get('deep_think_llm') or
                'gpt-4o-mini'
            )
            
            # 创建LLM配置
            llm_config = LLMConfig(
                provider=provider,
                model_name=model_name,
                api_key=api_key,
                api_base=legacy_config.get('openai_base_url') or legacy_config.get('backend_url'),
                temperature=float(legacy_config.get('llm_temperature', 0.7)),
                max_tokens=int(legacy_config.get('llm_max_tokens', 4000)) if legacy_config.get('llm_max_tokens') else None,
                timeout=30,
                retry_attempts=3,
                enabled=bool(api_key)
            )
            
            return llm_config.dict()
            
        except Exception as e:
            logger.error(f"转换LLM配置失败: {e}")
            return None
    
    def _convert_data_source_configs(self, legacy_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """转换数据源配置"""
        configs = []
        
        try:
            # Tushare配置
            tushare_token = legacy_config.get('tushare_token')
            if tushare_token:
                tushare_config = DataSourceConfig(
                    source_type=DataSourceType.TUSHARE,
                    api_key=tushare_token,
                    priority=1,
                    timeout=30,
                    cache_ttl=3600,
                    enabled=True
                )
                configs.append(tushare_config.dict())
            
            # AKShare配置（默认启用）
            akshare_config = DataSourceConfig(
                source_type=DataSourceType.AKSHARE,
                priority=2,
                timeout=30,
                cache_ttl=3600,
                enabled=True
            )
            configs.append(akshare_config.dict())
            
            # Finnhub配置
            finnhub_key = legacy_config.get('finnhub_api_key')
            if finnhub_key:
                finnhub_config = DataSourceConfig(
                    source_type=DataSourceType.FINNHUB,
                    api_key=finnhub_key,
                    priority=3,
                    timeout=30,
                    cache_ttl=3600,
                    enabled=True
                )
                configs.append(finnhub_config.dict())
            
            # BaoStock配置（默认启用）
            baostock_config = DataSourceConfig(
                source_type=DataSourceType.BAOSTOCK,
                priority=4,
                timeout=30,
                cache_ttl=3600,
                enabled=True
            )
            configs.append(baostock_config.dict())
            
            logger.info(f"转换了 {len(configs)} 个数据源配置")
            return configs
            
        except Exception as e:
            logger.error(f"转换数据源配置失败: {e}")
            return []
    
    def _convert_system_config(self, legacy_config: Dict[str, Any]) -> Dict[str, Any]:
        """转换系统配置"""
        try:
            system_config = SystemConfig(
                max_concurrent_analyses=int(legacy_config.get('max_recur_limit', 5)),
                default_analysis_timeout=1800,  # 30分钟
                cache_enabled=True,
                log_level=legacy_config.get('log_level', 'INFO').upper(),
                maintenance_mode=False
            )
            
            return system_config.dict()
            
        except Exception as e:
            logger.error(f"转换系统配置失败: {e}")
            return {}
    
    def _convert_user_preferences(self, legacy_config: Dict[str, Any]) -> Dict[str, Any]:
        """转换用户偏好配置"""
        try:
            preferences = {
                'default_market_type': 'cn',
                'preferred_analysts': [],
                'notification_enabled': True,
                'theme': 'light',
                'language': 'zh-CN',
                'online_tools_enabled': legacy_config.get('online_tools', False),
                'online_news_enabled': legacy_config.get('online_news', True),
                'realtime_data_enabled': legacy_config.get('realtime_data', False)
            }
            
            return preferences
            
        except Exception as e:
            logger.error(f"转换用户偏好配置失败: {e}")
            return {}
    
    def create_migration_backup(self, legacy_config: Dict[str, Any]) -> str:
        """创建配置迁移备份"""
        try:
            backup_dir = self.project_root / "config_backup"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"legacy_config_backup_{timestamp}.json"
            
            backup_data = {
                'timestamp': timestamp,
                'backup_reason': 'configuration_migration',
                'legacy_config': legacy_config,
                'migration_info': {
                    'source_files': [str(path) for path in self.legacy_config_paths if path.exists()],
                    'migration_date': datetime.now().isoformat()
                }
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"配置备份已创建: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            logger.error(f"创建配置备份失败: {e}")
            return ""
    
    def validate_config_compatibility(self, legacy_config: Dict[str, Any]) -> Dict[str, Any]:
        """验证配置兼容性"""
        validation_result = {
            'compatible': True,
            'warnings': [],
            'errors': [],
            'missing_required': [],
            'deprecated_keys': []
        }
        
        try:
            # 检查必需的配置项
            required_keys = ['llm_provider']
            for key in required_keys:
                if key not in legacy_config:
                    validation_result['missing_required'].append(key)
                    validation_result['compatible'] = False
            
            # 检查已弃用的配置项
            deprecated_keys = ['backend_url', 'max_recur_limit']
            for key in deprecated_keys:
                if key in legacy_config:
                    validation_result['deprecated_keys'].append(key)
                    validation_result['warnings'].append(f"配置项 '{key}' 已弃用，将被自动转换")
            
            # 检查LLM配置
            llm_provider = legacy_config.get('llm_provider', '').lower()
            if llm_provider and llm_provider not in ['openai', 'dashscope', 'deepseek', 'gemini', 'qianfan']:
                validation_result['errors'].append(f"不支持的LLM提供商: {llm_provider}")
                validation_result['compatible'] = False
            
            # 检查API密钥
            if llm_provider == 'openai' and not legacy_config.get('openai_api_key'):
                validation_result['warnings'].append("OpenAI API密钥未配置")
            
            logger.info(f"配置兼容性验证完成: {'兼容' if validation_result['compatible'] else '不兼容'}")
            return validation_result
            
        except Exception as e:
            logger.error(f"配置兼容性验证失败: {e}")
            validation_result['compatible'] = False
            validation_result['errors'].append(f"验证过程失败: {str(e)}")
            return validation_result


# 全局配置兼容性管理器实例
config_compatibility_manager = ConfigCompatibilityManager()


def load_and_convert_legacy_config() -> Dict[str, Any]:
    """加载并转换旧版配置的便捷函数"""
    try:
        # 加载旧版配置
        legacy_config = config_compatibility_manager.load_legacy_config()
        
        if not legacy_config:
            logger.warning("未找到旧版配置文件")
            return {}
        
        # 验证兼容性
        validation_result = config_compatibility_manager.validate_config_compatibility(legacy_config)
        
        if not validation_result['compatible']:
            logger.error(f"配置不兼容: {validation_result['errors']}")
            return {}
        
        # 创建备份
        backup_file = config_compatibility_manager.create_migration_backup(legacy_config)
        
        # 转换到新格式
        new_config = config_compatibility_manager.convert_to_new_format(legacy_config)
        
        logger.info("成功加载并转换旧版配置")
        return new_config
        
    except Exception as e:
        logger.error(f"加载和转换旧版配置失败: {e}")
        return {}