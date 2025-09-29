#!/usr/bin/env python3
"""
数据迁移验证脚本
验证迁移数据的完整性和正确性
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.core.database import get_database
from backend.core.redis_client import get_redis_client


@dataclass
class ValidationResult:
    """验证结果"""
    test_name: str
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class MigrationValidator:
    """迁移数据验证器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_results: List[ValidationResult] = []
    
    async def run_all_validations(self) -> List[ValidationResult]:
        """运行所有验证测试"""
        self.logger.info("开始验证迁移数据...")
        
        try:
            # 获取数据库和Redis连接
            db = await get_database()
            redis_client = await get_redis_client()
            
            # 运行各项验证测试
            await self._validate_database_structure(db)
            await self._validate_user_data(db)
            await self._validate_analysis_data(db)
            await self._validate_config_data(db)
            await self._validate_cache_data(redis_client)
            await self._validate_data_relationships(db)
            await self._validate_data_integrity(db)
            
            self.logger.info(f"验证完成，共 {len(self.validation_results)} 项测试")
            
        except Exception as e:
            self.logger.error(f"验证过程失败: {e}")
            self.validation_results.append(
                ValidationResult("validation_process", False, f"验证过程失败: {str(e)}")
            )
        
        return self.validation_results
    
    async def _validate_database_structure(self, db) -> None:
        """验证数据库结构"""
        try:
            # 检查必需的集合是否存在
            collections = await db.list_collection_names()
            required_collections = ['users', 'analyses', 'configs']
            
            for collection_name in required_collections:
                if collection_name in collections:
                    self.validation_results.append(
                        ValidationResult(
                            f"collection_{collection_name}_exists",
                            True,
                            f"集合 {collection_name} 存在"
                        )
                    )
                else:
                    self.validation_results.append(
                        ValidationResult(
                            f"collection_{collection_name}_exists",
                            False,
                            f"集合 {collection_name} 不存在"
                        )
                    )
            
            # 检查索引
            await self._validate_indexes(db)
            
        except Exception as e:
            self.validation_results.append(
                ValidationResult("database_structure", False, f"数据库结构验证失败: {str(e)}")
            )
    
    async def _validate_indexes(self, db) -> None:
        """验证数据库索引"""
        try:
            # 用户集合索引
            user_indexes = await db.users.list_indexes().to_list(None)
            username_index_exists = any(
                'username' in idx.get('key', {}) for idx in user_indexes
            )
            
            self.validation_results.append(
                ValidationResult(
                    "user_username_index",
                    username_index_exists,
                    f"用户名索引: {'存在' if username_index_exists else '不存在'}"
                )
            )
            
            # 分析集合索引
            analysis_indexes = await db.analyses.list_indexes().to_list(None)
            user_id_index_exists = any(
                'user_id' in idx.get('key', {}) for idx in analysis_indexes
            )
            
            self.validation_results.append(
                ValidationResult(
                    "analysis_user_id_index",
                    user_id_index_exists,
                    f"分析用户ID索引: {'存在' if user_id_index_exists else '不存在'}"
                )
            )
            
        except Exception as e:
            self.validation_results.append(
                ValidationResult("indexes_validation", False, f"索引验证失败: {str(e)}")
            )
    
    async def _validate_user_data(self, db) -> None:
        """验证用户数据"""
        try:
            users_collection = db.users
            
            # 检查用户总数
            total_users = await users_collection.count_documents({})
            self.validation_results.append(
                ValidationResult(
                    "user_count",
                    total_users > 0,
                    f"用户总数: {total_users}",
                    {"count": total_users}
                )
            )
            
            # 检查用户数据完整性
            users_without_username = await users_collection.count_documents({
                "$or": [
                    {"username": {"$exists": False}},
                    {"username": ""},
                    {"username": None}
                ]
            })
            
            self.validation_results.append(
                ValidationResult(
                    "user_username_integrity",
                    users_without_username == 0,
                    f"缺少用户名的用户: {users_without_username}",
                    {"invalid_count": users_without_username}
                )
            )
            
            # 检查用户名唯一性
            pipeline = [
                {"$group": {"_id": "$username", "count": {"$sum": 1}}},
                {"$match": {"count": {"$gt": 1}}}
            ]
            duplicate_usernames = await users_collection.aggregate(pipeline).to_list(None)
            
            self.validation_results.append(
                ValidationResult(
                    "user_username_uniqueness",
                    len(duplicate_usernames) == 0,
                    f"重复用户名数量: {len(duplicate_usernames)}",
                    {"duplicates": duplicate_usernames}
                )
            )
            
            # 检查密码哈希
            users_without_password = await users_collection.count_documents({
                "$or": [
                    {"password_hash": {"$exists": False}},
                    {"password_hash": ""},
                    {"password_hash": None}
                ]
            })
            
            self.validation_results.append(
                ValidationResult(
                    "user_password_integrity",
                    users_without_password == 0,
                    f"缺少密码哈希的用户: {users_without_password}",
                    {"invalid_count": users_without_password}
                )
            )
            
        except Exception as e:
            self.validation_results.append(
                ValidationResult("user_data_validation", False, f"用户数据验证失败: {str(e)}")
            )
    
    async def _validate_analysis_data(self, db) -> None:
        """验证分析数据"""
        try:
            analyses_collection = db.analyses
            
            # 检查分析记录总数
            total_analyses = await analyses_collection.count_documents({})
            self.validation_results.append(
                ValidationResult(
                    "analysis_count",
                    total_analyses >= 0,
                    f"分析记录总数: {total_analyses}",
                    {"count": total_analyses}
                )
            )
            
            if total_analyses > 0:
                # 检查分析数据完整性
                analyses_without_user = await analyses_collection.count_documents({
                    "$or": [
                        {"user_id": {"$exists": False}},
                        {"user_id": None}
                    ]
                })
                
                self.validation_results.append(
                    ValidationResult(
                        "analysis_user_id_integrity",
                        analyses_without_user == 0,
                        f"缺少用户ID的分析记录: {analyses_without_user}",
                        {"invalid_count": analyses_without_user}
                    )
                )
                
                # 检查股票代码
                analyses_without_stock_code = await analyses_collection.count_documents({
                    "$or": [
                        {"stock_code": {"$exists": False}},
                        {"stock_code": ""},
                        {"stock_code": None}
                    ]
                })
                
                self.validation_results.append(
                    ValidationResult(
                        "analysis_stock_code_integrity",
                        analyses_without_stock_code == 0,
                        f"缺少股票代码的分析记录: {analyses_without_stock_code}",
                        {"invalid_count": analyses_without_stock_code}
                    )
                )
                
                # 检查状态字段
                valid_statuses = ["pending", "running", "completed", "failed", "cancelled"]
                analyses_with_invalid_status = await analyses_collection.count_documents({
                    "status": {"$nin": valid_statuses}
                })
                
                self.validation_results.append(
                    ValidationResult(
                        "analysis_status_validity",
                        analyses_with_invalid_status == 0,
                        f"状态无效的分析记录: {analyses_with_invalid_status}",
                        {"invalid_count": analyses_with_invalid_status}
                    )
                )
                
                # 检查进度字段
                analyses_with_invalid_progress = await analyses_collection.count_documents({
                    "$or": [
                        {"progress": {"$lt": 0}},
                        {"progress": {"$gt": 100}}
                    ]
                })
                
                self.validation_results.append(
                    ValidationResult(
                        "analysis_progress_validity",
                        analyses_with_invalid_progress == 0,
                        f"进度无效的分析记录: {analyses_with_invalid_progress}",
                        {"invalid_count": analyses_with_invalid_progress}
                    )
                )
            
        except Exception as e:
            self.validation_results.append(
                ValidationResult("analysis_data_validation", False, f"分析数据验证失败: {str(e)}")
            )
    
    async def _validate_config_data(self, db) -> None:
        """验证配置数据"""
        try:
            configs_collection = db.configs
            
            # 检查配置记录总数
            total_configs = await configs_collection.count_documents({})
            self.validation_results.append(
                ValidationResult(
                    "config_count",
                    total_configs > 0,
                    f"配置记录总数: {total_configs}",
                    {"count": total_configs}
                )
            )
            
            # 检查系统配置
            system_configs = await configs_collection.count_documents({
                "user_id": None,
                "config_type": "system"
            })
            
            self.validation_results.append(
                ValidationResult(
                    "system_config_exists",
                    system_configs > 0,
                    f"系统配置数量: {system_configs}",
                    {"count": system_configs}
                )
            )
            
            # 检查LLM配置
            llm_configs = await configs_collection.count_documents({
                "config_type": "llm"
            })
            
            self.validation_results.append(
                ValidationResult(
                    "llm_config_exists",
                    llm_configs > 0,
                    f"LLM配置数量: {llm_configs}",
                    {"count": llm_configs}
                )
            )
            
            # 检查配置类型有效性
            valid_config_types = ["llm", "data_source", "system", "user_preference"]
            configs_with_invalid_type = await configs_collection.count_documents({
                "config_type": {"$nin": valid_config_types}
            })
            
            self.validation_results.append(
                ValidationResult(
                    "config_type_validity",
                    configs_with_invalid_type == 0,
                    f"配置类型无效的记录: {configs_with_invalid_type}",
                    {"invalid_count": configs_with_invalid_type}
                )
            )
            
        except Exception as e:
            self.validation_results.append(
                ValidationResult("config_data_validation", False, f"配置数据验证失败: {str(e)}")
            )
    
    async def _validate_cache_data(self, redis_client) -> None:
        """验证缓存数据"""
        try:
            # 检查Redis连接
            await redis_client.ping()
            
            self.validation_results.append(
                ValidationResult(
                    "redis_connection",
                    True,
                    "Redis连接正常"
                )
            )
            
            # 检查迁移的缓存条目
            migrated_cache_keys = await redis_client.keys("migrated_cache:*")
            
            self.validation_results.append(
                ValidationResult(
                    "migrated_cache_entries",
                    len(migrated_cache_keys) >= 0,
                    f"迁移的缓存条目数量: {len(migrated_cache_keys)}",
                    {"count": len(migrated_cache_keys)}
                )
            )
            
            # 检查缓存数据完整性（随机抽样）
            if migrated_cache_keys:
                sample_key = migrated_cache_keys[0]
                try:
                    cache_data = await redis_client.get(sample_key)
                    if cache_data:
                        json.loads(cache_data)  # 验证JSON格式
                        
                        self.validation_results.append(
                            ValidationResult(
                                "cache_data_format",
                                True,
                                "缓存数据格式正确"
                            )
                        )
                    else:
                        self.validation_results.append(
                            ValidationResult(
                                "cache_data_format",
                                False,
                                "缓存数据为空"
                            )
                        )
                except json.JSONDecodeError:
                    self.validation_results.append(
                        ValidationResult(
                            "cache_data_format",
                            False,
                            "缓存数据JSON格式无效"
                        )
                    )
            
        except Exception as e:
            self.validation_results.append(
                ValidationResult("cache_data_validation", False, f"缓存数据验证失败: {str(e)}")
            )
    
    async def _validate_data_relationships(self, db) -> None:
        """验证数据关系"""
        try:
            # 检查分析记录与用户的关系
            analyses_collection = db.analyses
            users_collection = db.users
            
            # 获取所有分析记录中的用户ID
            pipeline = [
                {"$group": {"_id": "$user_id"}},
                {"$match": {"_id": {"$ne": None}}}
            ]
            analysis_user_ids = await analyses_collection.aggregate(pipeline).to_list(None)
            analysis_user_ids = [item["_id"] for item in analysis_user_ids]
            
            # 检查这些用户ID是否都存在于用户集合中
            orphaned_analyses = 0
            for user_id in analysis_user_ids:
                user_exists = await users_collection.count_documents({"_id": user_id}) > 0
                if not user_exists:
                    orphaned_analyses += 1
            
            self.validation_results.append(
                ValidationResult(
                    "analysis_user_relationship",
                    orphaned_analyses == 0,
                    f"孤立的分析记录（用户不存在）: {orphaned_analyses}",
                    {"orphaned_count": orphaned_analyses}
                )
            )
            
            # 检查配置记录与用户的关系
            configs_collection = db.configs
            user_configs = await configs_collection.find({"user_id": {"$ne": None}}).to_list(None)
            
            orphaned_configs = 0
            for config in user_configs:
                user_exists = await users_collection.count_documents({"_id": config["user_id"]}) > 0
                if not user_exists:
                    orphaned_configs += 1
            
            self.validation_results.append(
                ValidationResult(
                    "config_user_relationship",
                    orphaned_configs == 0,
                    f"孤立的配置记录（用户不存在）: {orphaned_configs}",
                    {"orphaned_count": orphaned_configs}
                )
            )
            
        except Exception as e:
            self.validation_results.append(
                ValidationResult("data_relationships_validation", False, f"数据关系验证失败: {str(e)}")
            )
    
    async def _validate_data_integrity(self, db) -> None:
        """验证数据完整性"""
        try:
            # 检查时间戳的合理性
            analyses_collection = db.analyses
            
            # 检查创建时间不能是未来时间
            future_analyses = await analyses_collection.count_documents({
                "created_at": {"$gt": datetime.utcnow()}
            })
            
            self.validation_results.append(
                ValidationResult(
                    "analysis_created_at_validity",
                    future_analyses == 0,
                    f"创建时间为未来的分析记录: {future_analyses}",
                    {"invalid_count": future_analyses}
                )
            )
            
            # 检查完成时间不能早于创建时间
            invalid_completion_time = await analyses_collection.count_documents({
                "$and": [
                    {"completed_at": {"$exists": True, "$ne": None}},
                    {"$expr": {"$lt": ["$completed_at", "$created_at"]}}
                ]
            })
            
            self.validation_results.append(
                ValidationResult(
                    "analysis_completion_time_validity",
                    invalid_completion_time == 0,
                    f"完成时间早于创建时间的记录: {invalid_completion_time}",
                    {"invalid_count": invalid_completion_time}
                )
            )
            
            # 检查已完成的分析是否有结果数据
            completed_without_results = await analyses_collection.count_documents({
                "status": "completed",
                "$or": [
                    {"result_data": {"$exists": False}},
                    {"result_data": None}
                ]
            })
            
            self.validation_results.append(
                ValidationResult(
                    "completed_analysis_has_results",
                    completed_without_results == 0,
                    f"已完成但无结果数据的分析: {completed_without_results}",
                    {"invalid_count": completed_without_results}
                )
            )
            
        except Exception as e:
            self.validation_results.append(
                ValidationResult("data_integrity_validation", False, f"数据完整性验证失败: {str(e)}")
            )
    
    def generate_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        passed_tests = sum(1 for result in self.validation_results if result.passed)
        total_tests = len(self.validation_results)
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "results": [
                {
                    "test_name": result.test_name,
                    "passed": result.passed,
                    "message": result.message,
                    "details": result.details
                }
                for result in self.validation_results
            ],
            "failed_tests": [
                {
                    "test_name": result.test_name,
                    "message": result.message,
                    "details": result.details
                }
                for result in self.validation_results if not result.passed
            ]
        }
        
        return report


async def main():
    """主函数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    validator = MigrationValidator()
    
    # 运行验证
    results = await validator.run_all_validations()
    
    # 生成报告
    report = validator.generate_report()
    
    # 输出结果
    print("\n=== 数据迁移验证报告 ===")
    print(f"总测试数: {report['summary']['total_tests']}")
    print(f"通过测试: {report['summary']['passed_tests']}")
    print(f"失败测试: {report['summary']['failed_tests']}")
    print(f"成功率: {report['summary']['success_rate']:.1f}%")
    
    if report['failed_tests']:
        print(f"\n=== 失败的测试 ===")
        for failed_test in report['failed_tests']:
            print(f"✗ {failed_test['test_name']}: {failed_test['message']}")
            if failed_test['details']:
                print(f"  详情: {failed_test['details']}")
    
    print(f"\n=== 所有测试结果 ===")
    for result in results:
        status_symbol = "✓" if result.passed else "✗"
        print(f"{status_symbol} {result.test_name}: {result.message}")
    
    # 保存报告到文件
    report_file = project_root / "migration_validation_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n详细报告已保存到: {report_file}")
    
    # 如果有失败的测试，返回非零退出码
    if report['summary']['failed_tests'] > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())