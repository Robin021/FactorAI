#!/usr/bin/env python3
"""
分析结果数据迁移脚本
将现有的分析结果和缓存数据迁移到新的数据格式
"""

import os
import sys
import json
import asyncio
import pickle
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.models.analysis import AnalysisResult
from backend.core.database import get_database
from backend.core.redis_client import get_redis_client


@dataclass
class AnalysisResultsMigrationStats:
    """分析结果迁移统计信息"""
    results_migrated: int = 0
    cache_entries_migrated: int = 0
    reports_migrated: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class AnalysisResultsMigrator:
    """分析结果迁移器"""
    
    def __init__(self, data_dir: Path = None):
        self.logger = logging.getLogger(__name__)
        self.data_dir = data_dir or project_root / "data"
        self.stats = AnalysisResultsMigrationStats()
        
    async def migrate_all_results(self) -> AnalysisResultsMigrationStats:
        """迁移所有分析结果数据"""
        self.logger.info("开始迁移分析结果数据...")
        
        try:
            # 获取数据库和Redis连接
            db = await get_database()
            redis_client = await get_redis_client()
            
            # 1. 迁移分析结果文件
            await self._migrate_analysis_results(db)
            
            # 2. 迁移缓存数据
            await self._migrate_cache_data(redis_client)
            
            # 3. 迁移报告文件
            await self._migrate_reports(db)
            
            self.logger.info(f"分析结果迁移完成: {self.stats}")
            
        except Exception as e:
            self.logger.error(f"分析结果迁移失败: {e}")
            self.stats.errors.append(f"Migration failed: {str(e)}")
            
        return self.stats
    
    async def _migrate_analysis_results(self, db) -> None:
        """迁移分析结果文件"""
        self.logger.info("开始迁移分析结果文件...")
        
        try:
            results_dir = self.data_dir / "analysis_results"
            if not results_dir.exists():
                self.logger.warning(f"分析结果目录不存在: {results_dir}")
                return
            
            analyses_collection = db.analyses
            
            # 遍历所有结果文件
            for result_file in results_dir.rglob("*.json"):
                try:
                    await self._process_result_file(result_file, analyses_collection)
                except Exception as e:
                    error_msg = f"处理结果文件失败 {result_file}: {str(e)}"
                    self.logger.error(error_msg)
                    self.stats.errors.append(error_msg)
                    
        except Exception as e:
            error_msg = f"分析结果迁移失败: {str(e)}"
            self.logger.error(error_msg)
            self.stats.errors.append(error_msg)
    
    async def _process_result_file(self, result_file: Path, analyses_collection) -> None:
        """处理单个结果文件"""
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
            
            # 从文件名或数据中提取股票代码和时间戳
            stock_code = self._extract_stock_code_from_filename(result_file.name)
            if not stock_code:
                stock_code = result_data.get('stock_code', 'UNKNOWN')
            
            # 转换结果数据格式
            converted_result = await self._convert_result_format(result_data)
            
            # 查找对应的分析记录
            analysis_record = await analyses_collection.find_one({
                "stock_code": stock_code,
                "status": "completed"
            }, sort=[("created_at", -1)])  # 获取最新的完成记录
            
            if analysis_record:
                # 更新现有记录的结果数据
                await analyses_collection.update_one(
                    {"_id": analysis_record["_id"]},
                    {"$set": {"result_data": converted_result.dict()}}
                )
                self.stats.results_migrated += 1
                self.logger.info(f"更新分析结果: {stock_code}")
            else:
                # 创建新的分析记录（如果没有找到对应记录）
                from backend.models.analysis import AnalysisInDB, AnalysisStatus, MarketType
                from bson import ObjectId
                
                # 创建默认用户ID（需要先确保有默认用户）
                default_user = await analyses_collection.database.users.find_one({"username": "migrated_user"})
                if not default_user:
                    # 创建迁移用户
                    from backend.models.user import UserInDB, UserRole
                    from backend.utils.security import get_password_hash
                    
                    migrated_user = UserInDB(
                        username="migrated_user",
                        email="migrated@example.com",
                        role=UserRole.USER,
                        password_hash=get_password_hash("changeme123"),
                        created_at=datetime.utcnow(),
                        is_active=True
                    )
                    
                    result = await analyses_collection.database.users.insert_one(
                        migrated_user.dict(by_alias=True)
                    )
                    default_user_id = result.inserted_id
                else:
                    default_user_id = default_user["_id"]
                
                # 创建分析记录
                analysis_doc = AnalysisInDB(
                    user_id=default_user_id,
                    stock_code=stock_code,
                    market_type=self._detect_market_type(stock_code),
                    status=AnalysisStatus.COMPLETED,
                    progress=100.0,
                    config={"migrated_from_file": str(result_file)},
                    result_data=converted_result,
                    created_at=datetime.fromtimestamp(result_file.stat().st_mtime),
                    completed_at=datetime.fromtimestamp(result_file.stat().st_mtime)
                )
                
                await analyses_collection.insert_one(analysis_doc.dict(by_alias=True))
                self.stats.results_migrated += 1
                self.logger.info(f"创建新分析记录: {stock_code}")
                
        except Exception as e:
            error_msg = f"处理结果文件失败 {result_file}: {str(e)}"
            self.logger.error(error_msg)
            self.stats.errors.append(error_msg)
    
    def _extract_stock_code_from_filename(self, filename: str) -> Optional[str]:
        """从文件名中提取股票代码"""
        try:
            # 常见的文件名格式: stock_000001_20240101.json, analysis_AAPL_result.json 等
            parts = filename.replace('.json', '').split('_')
            
            for part in parts:
                # 检查是否是股票代码格式
                if part.isdigit() and len(part) == 6:  # A股代码
                    return part
                elif part.isalpha() and 1 <= len(part) <= 5:  # 美股代码
                    return part.upper()
                elif part.startswith('HK') or (part.isdigit() and len(part) == 5):  # 港股代码
                    return part
            
            return None
            
        except Exception:
            return None
    
    def _detect_market_type(self, stock_code: str):
        """检测市场类型"""
        from backend.models.analysis import MarketType
        
        if not stock_code:
            return MarketType.CN
        
        stock_code = stock_code.upper()
        
        # 港股
        if stock_code.startswith('HK') or (stock_code.isdigit() and len(stock_code) == 5):
            return MarketType.HK
        
        # 美股
        if stock_code.isalpha() and len(stock_code) <= 5:
            return MarketType.US
        
        # 默认A股
        return MarketType.CN
    
    async def _convert_result_format(self, old_result: Dict[str, Any]) -> AnalysisResult:
        """转换结果数据格式"""
        try:
            # 创建新格式的分析结果
            converted_result = AnalysisResult()
            
            # 映射旧格式到新格式
            if 'summary' in old_result:
                converted_result.summary = old_result['summary']
            
            if 'technical_analysis' in old_result:
                converted_result.technical_analysis = old_result['technical_analysis']
            elif 'technical' in old_result:
                converted_result.technical_analysis = old_result['technical']
            
            if 'fundamental_analysis' in old_result:
                converted_result.fundamental_analysis = old_result['fundamental_analysis']
            elif 'fundamental' in old_result:
                converted_result.fundamental_analysis = old_result['fundamental']
            
            if 'news_analysis' in old_result:
                converted_result.news_analysis = old_result['news_analysis']
            elif 'news' in old_result:
                converted_result.news_analysis = old_result['news']
            
            if 'risk_assessment' in old_result:
                converted_result.risk_assessment = old_result['risk_assessment']
            elif 'risk' in old_result:
                converted_result.risk_assessment = old_result['risk']
            
            if 'charts' in old_result:
                converted_result.charts = old_result['charts']
            
            # 保存原始数据
            converted_result.raw_data = {
                'original_format': old_result,
                'migrated_at': datetime.utcnow().isoformat()
            }
            
            return converted_result
            
        except Exception as e:
            self.logger.error(f"转换结果格式失败: {e}")
            # 返回包含原始数据的结果
            return AnalysisResult(raw_data={'original_format': old_result})
    
    async def _migrate_cache_data(self, redis_client) -> None:
        """迁移缓存数据"""
        self.logger.info("开始迁移缓存数据...")
        
        try:
            cache_dir = self.data_dir / "cache"
            if not cache_dir.exists():
                self.logger.warning(f"缓存目录不存在: {cache_dir}")
                return
            
            # 遍历缓存文件
            for cache_file in cache_dir.rglob("*"):
                if cache_file.is_file():
                    try:
                        await self._process_cache_file(cache_file, redis_client)
                    except Exception as e:
                        error_msg = f"处理缓存文件失败 {cache_file}: {str(e)}"
                        self.logger.error(error_msg)
                        self.stats.errors.append(error_msg)
                        
        except Exception as e:
            error_msg = f"缓存数据迁移失败: {str(e)}"
            self.logger.error(error_msg)
            self.stats.errors.append(error_msg)
    
    async def _process_cache_file(self, cache_file: Path, redis_client) -> None:
        """处理单个缓存文件"""
        try:
            # 根据文件扩展名处理不同类型的缓存文件
            if cache_file.suffix == '.json':
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
            elif cache_file.suffix == '.pkl':
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
            else:
                # 跳过不支持的文件类型
                return
            
            # 生成Redis键名
            cache_key = f"migrated_cache:{cache_file.stem}"
            
            # 存储到Redis
            await redis_client.setex(
                cache_key,
                3600 * 24 * 7,  # 7天过期
                json.dumps(cache_data, default=str, ensure_ascii=False)
            )
            
            self.stats.cache_entries_migrated += 1
            self.logger.info(f"迁移缓存文件: {cache_file.name}")
            
        except Exception as e:
            error_msg = f"处理缓存文件失败 {cache_file}: {str(e)}"
            self.logger.error(error_msg)
            self.stats.errors.append(error_msg)
    
    async def _migrate_reports(self, db) -> None:
        """迁移报告文件"""
        self.logger.info("开始迁移报告文件...")
        
        try:
            reports_dir = self.data_dir / "reports"
            if not reports_dir.exists():
                self.logger.warning(f"报告目录不存在: {reports_dir}")
                return
            
            # 创建报告集合（如果需要的话）
            reports_collection = db.reports
            
            # 遍历报告文件
            for report_file in reports_dir.rglob("*.md"):
                try:
                    await self._process_report_file(report_file, reports_collection)
                except Exception as e:
                    error_msg = f"处理报告文件失败 {report_file}: {str(e)}"
                    self.logger.error(error_msg)
                    self.stats.errors.append(error_msg)
                    
        except Exception as e:
            error_msg = f"报告迁移失败: {str(e)}"
            self.logger.error(error_msg)
            self.stats.errors.append(error_msg)
    
    async def _process_report_file(self, report_file: Path, reports_collection) -> None:
        """处理单个报告文件"""
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                report_content = f.read()
            
            # 创建报告记录
            report_doc = {
                'filename': report_file.name,
                'content': report_content,
                'file_path': str(report_file),
                'created_at': datetime.fromtimestamp(report_file.stat().st_mtime),
                'migrated_at': datetime.utcnow(),
                'file_size': report_file.stat().st_size
            }
            
            # 检查是否已存在
            existing_report = await reports_collection.find_one({
                'filename': report_file.name,
                'file_path': str(report_file)
            })
            
            if not existing_report:
                await reports_collection.insert_one(report_doc)
                self.stats.reports_migrated += 1
                self.logger.info(f"迁移报告文件: {report_file.name}")
            
        except Exception as e:
            error_msg = f"处理报告文件失败 {report_file}: {str(e)}"
            self.logger.error(error_msg)
            self.stats.errors.append(error_msg)
    
    async def validate_migration(self) -> Dict[str, Any]:
        """验证迁移结果"""
        self.logger.info("开始验证分析结果迁移...")
        
        validation_results = {
            'analyses_with_results': 0,
            'cache_entries': 0,
            'reports_count': 0,
            'validation_errors': []
        }
        
        try:
            db = await get_database()
            redis_client = await get_redis_client()
            
            # 验证分析结果
            analyses_with_results = await db.analyses.count_documents({
                "result_data": {"$exists": True, "$ne": None}
            })
            validation_results['analyses_with_results'] = analyses_with_results
            
            # 验证缓存条目
            cache_keys = await redis_client.keys("migrated_cache:*")
            validation_results['cache_entries'] = len(cache_keys)
            
            # 验证报告
            if 'reports' in await db.list_collection_names():
                reports_count = await db.reports.count_documents({})
                validation_results['reports_count'] = reports_count
            
            self.logger.info(f"分析结果验证完成: {validation_results}")
            
        except Exception as e:
            error_msg = f"验证失败: {str(e)}"
            self.logger.error(error_msg)
            validation_results['validation_errors'].append(error_msg)
        
        return validation_results


async def main():
    """主函数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    migrator = AnalysisResultsMigrator()
    
    # 执行迁移
    stats = await migrator.migrate_all_results()
    
    print("\n=== 分析结果迁移统计 ===")
    print(f"结果文件迁移数量: {stats.results_migrated}")
    print(f"缓存条目迁移数量: {stats.cache_entries_migrated}")
    print(f"报告文件迁移数量: {stats.reports_migrated}")
    
    if stats.errors:
        print(f"\n错误数量: {len(stats.errors)}")
        for error in stats.errors[:10]:
            print(f"  - {error}")
    
    # 验证迁移结果
    validation_results = await migrator.validate_migration()
    
    print("\n=== 验证结果 ===")
    print(f"包含结果的分析记录: {validation_results['analyses_with_results']}")
    print(f"缓存条目数量: {validation_results['cache_entries']}")
    print(f"报告数量: {validation_results['reports_count']}")
    
    if validation_results['validation_errors']:
        print(f"\n验证错误: {len(validation_results['validation_errors'])}")
        for error in validation_results['validation_errors']:
            print(f"  - {error}")


if __name__ == "__main__":
    asyncio.run(main())