#!/usr/bin/env python3
"""
Streamlit用户数据迁移脚本
将现有的Streamlit用户数据迁移到新的FastAPI+React架构
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.models.user import UserInDB, UserRole
from backend.models.analysis import AnalysisInDB, AnalysisStatus, MarketType
from backend.models.config import ConfigInDB, ConfigType
from backend.core.database import get_database
from backend.utils.security import get_password_hash


@dataclass
class MigrationStats:
    """迁移统计信息"""
    users_migrated: int = 0
    analyses_migrated: int = 0
    configs_migrated: int = 0
    activities_migrated: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class StreamlitDataMigrator:
    """Streamlit数据迁移器"""
    
    def __init__(self, web_data_dir: Path = None):
        self.logger = logging.getLogger(__name__)
        self.web_data_dir = web_data_dir or project_root / "web" / "data"
        self.stats = MigrationStats()
        
    async def migrate_all_data(self) -> MigrationStats:
        """迁移所有数据"""
        self.logger.info("开始迁移Streamlit数据到新架构...")
        
        try:
            # 获取数据库连接
            db = await get_database()
            
            # 1. 迁移用户数据
            await self._migrate_users(db)
            
            # 2. 迁移用户活动记录为分析历史
            await self._migrate_user_activities(db)
            
            # 3. 迁移配置数据
            await self._migrate_configurations(db)
            
            # 4. 迁移缓存数据
            await self._migrate_cache_data(db)
            
            self.logger.info(f"数据迁移完成: {self.stats}")
            
        except Exception as e:
            self.logger.error(f"数据迁移失败: {e}")
            self.stats.errors.append(f"Migration failed: {str(e)}")
            
        return self.stats
    
    async def _migrate_users(self, db) -> None:
        """迁移用户数据"""
        self.logger.info("开始迁移用户数据...")
        
        try:
            # 从用户活动日志中提取用户信息
            users_data = await self._extract_users_from_activities()
            
            users_collection = db.users
            
            for username, user_info in users_data.items():
                try:
                    # 检查用户是否已存在
                    existing_user = await users_collection.find_one({"username": username})
                    if existing_user:
                        self.logger.info(f"用户 {username} 已存在，跳过")
                        continue
                    
                    # 创建新用户
                    user_doc = UserInDB(
                        username=username,
                        email=user_info.get("email"),
                        role=UserRole.USER,  # 默认为普通用户
                        password_hash=get_password_hash("changeme123"),  # 默认密码
                        created_at=user_info.get("first_seen", datetime.utcnow()),
                        last_login=user_info.get("last_seen"),
                        is_active=True
                    )
                    
                    result = await users_collection.insert_one(user_doc.dict(by_alias=True))
                    self.logger.info(f"成功迁移用户: {username} (ID: {result.inserted_id})")
                    self.stats.users_migrated += 1
                    
                except Exception as e:
                    error_msg = f"迁移用户 {username} 失败: {str(e)}"
                    self.logger.error(error_msg)
                    self.stats.errors.append(error_msg)
                    
        except Exception as e:
            error_msg = f"用户数据迁移失败: {str(e)}"
            self.logger.error(error_msg)
            self.stats.errors.append(error_msg)
    
    async def _extract_users_from_activities(self) -> Dict[str, Dict[str, Any]]:
        """从用户活动日志中提取用户信息"""
        users_data = {}
        activities_dir = self.web_data_dir / "user_activities"
        
        if not activities_dir.exists():
            self.logger.warning(f"用户活动目录不存在: {activities_dir}")
            return users_data
        
        for activity_file in activities_dir.glob("user_activities_*.jsonl"):
            try:
                with open(activity_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            activity = json.loads(line.strip())
                            username = activity.get('username', 'unknown')
                            
                            if username not in users_data:
                                users_data[username] = {
                                    'first_seen': datetime.fromtimestamp(activity['timestamp']),
                                    'last_seen': datetime.fromtimestamp(activity['timestamp']),
                                    'activity_count': 0
                                }
                            
                            # 更新用户信息
                            user_info = users_data[username]
                            activity_time = datetime.fromtimestamp(activity['timestamp'])
                            
                            if activity_time < user_info['first_seen']:
                                user_info['first_seen'] = activity_time
                            if activity_time > user_info['last_seen']:
                                user_info['last_seen'] = activity_time
                            
                            user_info['activity_count'] += 1
                            
            except Exception as e:
                self.logger.error(f"读取活动文件失败 {activity_file}: {e}")
        
        return users_data
    
    async def _migrate_user_activities(self, db) -> None:
        """迁移用户活动记录为分析历史"""
        self.logger.info("开始迁移用户活动记录...")
        
        try:
            activities_dir = self.web_data_dir / "user_activities"
            if not activities_dir.exists():
                self.logger.warning(f"用户活动目录不存在: {activities_dir}")
                return
            
            users_collection = db.users
            analyses_collection = db.analyses
            
            for activity_file in activities_dir.glob("user_activities_*.jsonl"):
                try:
                    with open(activity_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                activity = json.loads(line.strip())
                                await self._process_activity_record(
                                    activity, users_collection, analyses_collection
                                )
                                
                except Exception as e:
                    error_msg = f"处理活动文件失败 {activity_file}: {str(e)}"
                    self.logger.error(error_msg)
                    self.stats.errors.append(error_msg)
                    
        except Exception as e:
            error_msg = f"用户活动迁移失败: {str(e)}"
            self.logger.error(error_msg)
            self.stats.errors.append(error_msg)
    
    async def _process_activity_record(self, activity: Dict[str, Any], 
                                     users_collection, analyses_collection) -> None:
        """处理单个活动记录"""
        try:
            # 只处理股票分析相关的活动
            action_name = activity.get('action_name', '')
            if 'analysis' not in action_name.lower() and 'stock' not in action_name.lower():
                return
            
            username = activity.get('username', 'unknown')
            
            # 查找用户ID
            user = await users_collection.find_one({"username": username})
            if not user:
                self.logger.warning(f"未找到用户: {username}")
                return
            
            # 提取股票代码和分析参数
            details = activity.get('details', {})
            stock_code = details.get('stock_code') or details.get('symbol', '')
            
            if not stock_code:
                return  # 没有股票代码的活动不迁移
            
            # 创建分析记录
            analysis_doc = AnalysisInDB(
                user_id=user['_id'],
                stock_code=stock_code,
                market_type=self._detect_market_type(stock_code),
                status=AnalysisStatus.COMPLETED if activity.get('success', True) else AnalysisStatus.FAILED,
                progress=100.0 if activity.get('success', True) else 0.0,
                config={
                    'migrated_from_streamlit': True,
                    'original_activity': activity
                },
                created_at=datetime.fromtimestamp(activity['timestamp']),
                completed_at=datetime.fromtimestamp(activity['timestamp']) if activity.get('success', True) else None,
                error_message=details.get('error') if not activity.get('success', True) else None
            )
            
            # 检查是否已存在相同的分析记录
            existing = await analyses_collection.find_one({
                "user_id": user['_id'],
                "stock_code": stock_code,
                "created_at": analysis_doc.created_at
            })
            
            if not existing:
                await analyses_collection.insert_one(analysis_doc.dict(by_alias=True))
                self.stats.analyses_migrated += 1
                
        except Exception as e:
            error_msg = f"处理活动记录失败: {str(e)}"
            self.logger.error(error_msg)
            self.stats.errors.append(error_msg)
    
    def _detect_market_type(self, stock_code: str) -> MarketType:
        """根据股票代码检测市场类型"""
        if not stock_code:
            return MarketType.CN
        
        stock_code = stock_code.upper()
        
        # 港股
        if stock_code.startswith('HK') or (stock_code.isdigit() and len(stock_code) == 5):
            return MarketType.HK
        
        # 美股 (通常是字母)
        if stock_code.isalpha() and len(stock_code) <= 5:
            return MarketType.US
        
        # 默认A股
        return MarketType.CN
    
    async def _migrate_configurations(self, db) -> None:
        """迁移配置数据"""
        self.logger.info("开始迁移配置数据...")
        
        try:
            # 迁移默认配置
            await self._migrate_default_config(db)
            
            # 迁移环境变量配置
            await self._migrate_env_config(db)
            
        except Exception as e:
            error_msg = f"配置数据迁移失败: {str(e)}"
            self.logger.error(error_msg)
            self.stats.errors.append(error_msg)
    
    async def _migrate_default_config(self, db) -> None:
        """迁移默认配置"""
        try:
            from tradingagents.default_config import DEFAULT_CONFIG
            
            configs_collection = db.configs
            
            # 检查是否已存在系统配置
            existing_config = await configs_collection.find_one({
                "user_id": None,
                "config_type": ConfigType.SYSTEM
            })
            
            if existing_config:
                self.logger.info("系统配置已存在，跳过迁移")
                return
            
            # 创建系统配置
            system_config = ConfigInDB(
                user_id=None,  # 系统级配置
                config_type=ConfigType.SYSTEM,
                config_data={
                    'max_concurrent_analyses': 5,
                    'default_analysis_timeout': 1800,
                    'cache_enabled': True,
                    'log_level': 'INFO',
                    'maintenance_mode': False,
                    'migrated_from_default_config': DEFAULT_CONFIG
                }
            )
            
            await configs_collection.insert_one(system_config.dict(by_alias=True))
            self.stats.configs_migrated += 1
            self.logger.info("成功迁移系统默认配置")
            
        except Exception as e:
            error_msg = f"迁移默认配置失败: {str(e)}"
            self.logger.error(error_msg)
            self.stats.errors.append(error_msg)
    
    async def _migrate_env_config(self, db) -> None:
        """迁移环境变量配置"""
        try:
            configs_collection = db.configs
            
            # LLM配置
            llm_config_data = {
                'provider': os.getenv('LLM_PROVIDER', 'openai'),
                'model_name': os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                'api_key': os.getenv('OPENAI_API_KEY', ''),
                'api_base': os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
                'temperature': float(os.getenv('LLM_TEMPERATURE', '0.7')),
                'max_tokens': int(os.getenv('LLM_MAX_TOKENS', '4000')) if os.getenv('LLM_MAX_TOKENS') else None,
                'timeout': int(os.getenv('LLM_TIMEOUT', '30')),
                'enabled': True
            }
            
            # 检查LLM配置是否已存在
            existing_llm_config = await configs_collection.find_one({
                "user_id": None,
                "config_type": ConfigType.LLM
            })
            
            if not existing_llm_config:
                llm_config = ConfigInDB(
                    user_id=None,
                    config_type=ConfigType.LLM,
                    config_data=llm_config_data
                )
                await configs_collection.insert_one(llm_config.dict(by_alias=True))
                self.stats.configs_migrated += 1
                self.logger.info("成功迁移LLM配置")
            
            # 数据源配置
            data_source_config_data = {
                'tushare': {
                    'api_key': os.getenv('TUSHARE_TOKEN', ''),
                    'priority': 1,
                    'enabled': bool(os.getenv('TUSHARE_TOKEN'))
                },
                'akshare': {
                    'priority': 2,
                    'enabled': True
                },
                'finnhub': {
                    'api_key': os.getenv('FINNHUB_API_KEY', ''),
                    'priority': 3,
                    'enabled': bool(os.getenv('FINNHUB_API_KEY'))
                }
            }
            
            # 检查数据源配置是否已存在
            existing_ds_config = await configs_collection.find_one({
                "user_id": None,
                "config_type": ConfigType.DATA_SOURCE
            })
            
            if not existing_ds_config:
                ds_config = ConfigInDB(
                    user_id=None,
                    config_type=ConfigType.DATA_SOURCE,
                    config_data=data_source_config_data
                )
                await configs_collection.insert_one(ds_config.dict(by_alias=True))
                self.stats.configs_migrated += 1
                self.logger.info("成功迁移数据源配置")
                
        except Exception as e:
            error_msg = f"迁移环境变量配置失败: {str(e)}"
            self.logger.error(error_msg)
            self.stats.errors.append(error_msg)
    
    async def _migrate_cache_data(self, db) -> None:
        """迁移缓存数据"""
        self.logger.info("开始迁移缓存数据...")
        
        try:
            # 这里主要是清理和重建缓存索引
            # 实际的缓存数据在Redis中，不需要迁移到MongoDB
            
            # 可以在这里添加Redis缓存的清理逻辑
            self.logger.info("缓存数据迁移完成（主要是清理工作）")
            
        except Exception as e:
            error_msg = f"缓存数据迁移失败: {str(e)}"
            self.logger.error(error_msg)
            self.stats.errors.append(error_msg)
    
    async def validate_migration(self) -> Dict[str, Any]:
        """验证迁移数据的完整性和正确性"""
        self.logger.info("开始验证迁移数据...")
        
        validation_results = {
            'users_count': 0,
            'analyses_count': 0,
            'configs_count': 0,
            'validation_errors': []
        }
        
        try:
            db = await get_database()
            
            # 验证用户数据
            users_count = await db.users.count_documents({})
            validation_results['users_count'] = users_count
            
            # 验证分析数据
            analyses_count = await db.analyses.count_documents({})
            validation_results['analyses_count'] = analyses_count
            
            # 验证配置数据
            configs_count = await db.configs.count_documents({})
            validation_results['configs_count'] = configs_count
            
            # 验证数据完整性
            await self._validate_data_integrity(db, validation_results)
            
            self.logger.info(f"数据验证完成: {validation_results}")
            
        except Exception as e:
            error_msg = f"数据验证失败: {str(e)}"
            self.logger.error(error_msg)
            validation_results['validation_errors'].append(error_msg)
        
        return validation_results
    
    async def _validate_data_integrity(self, db, validation_results: Dict[str, Any]) -> None:
        """验证数据完整性"""
        try:
            # 检查用户数据完整性
            users_without_username = await db.users.count_documents({"username": {"$exists": False}})
            if users_without_username > 0:
                validation_results['validation_errors'].append(
                    f"发现 {users_without_username} 个用户缺少用户名"
                )
            
            # 检查分析数据完整性
            analyses_without_user = await db.analyses.count_documents({"user_id": {"$exists": False}})
            if analyses_without_user > 0:
                validation_results['validation_errors'].append(
                    f"发现 {analyses_without_user} 个分析记录缺少用户ID"
                )
            
            # 检查配置数据完整性
            configs_without_type = await db.configs.count_documents({"config_type": {"$exists": False}})
            if configs_without_type > 0:
                validation_results['validation_errors'].append(
                    f"发现 {configs_without_type} 个配置记录缺少配置类型"
                )
            
        except Exception as e:
            validation_results['validation_errors'].append(f"数据完整性检查失败: {str(e)}")


async def main():
    """主函数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    migrator = StreamlitDataMigrator()
    
    # 执行迁移
    stats = await migrator.migrate_all_data()
    
    print("\n=== 迁移统计 ===")
    print(f"用户迁移数量: {stats.users_migrated}")
    print(f"分析记录迁移数量: {stats.analyses_migrated}")
    print(f"配置迁移数量: {stats.configs_migrated}")
    print(f"活动记录迁移数量: {stats.activities_migrated}")
    
    if stats.errors:
        print(f"\n错误数量: {len(stats.errors)}")
        for error in stats.errors[:10]:  # 只显示前10个错误
            print(f"  - {error}")
    
    # 验证迁移结果
    validation_results = await migrator.validate_migration()
    
    print("\n=== 验证结果 ===")
    print(f"用户总数: {validation_results['users_count']}")
    print(f"分析记录总数: {validation_results['analyses_count']}")
    print(f"配置总数: {validation_results['configs_count']}")
    
    if validation_results['validation_errors']:
        print(f"\n验证错误: {len(validation_results['validation_errors'])}")
        for error in validation_results['validation_errors']:
            print(f"  - {error}")


if __name__ == "__main__":
    asyncio.run(main())