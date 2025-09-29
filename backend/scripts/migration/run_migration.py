#!/usr/bin/env python3
"""
数据迁移主脚本
统一执行所有数据迁移任务
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from streamlit_data_migrator import StreamlitDataMigrator
from analysis_results_migrator import AnalysisResultsMigrator


class MigrationRunner:
    """迁移运行器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.migration_log_file = project_root / "migration_log.txt"
        
    async def run_full_migration(self, skip_existing: bool = True) -> Dict[str, Any]:
        """运行完整的数据迁移"""
        self.logger.info("开始完整数据迁移...")
        
        migration_results = {
            'start_time': datetime.utcnow(),
            'streamlit_migration': None,
            'results_migration': None,
            'validation_results': None,
            'end_time': None,
            'success': False,
            'errors': []
        }
        
        try:
            # 1. 迁移Streamlit用户数据
            self.logger.info("=== 第1步: 迁移Streamlit用户数据 ===")
            streamlit_migrator = StreamlitDataMigrator()
            streamlit_stats = await streamlit_migrator.migrate_all_data()
            migration_results['streamlit_migration'] = {
                'users_migrated': streamlit_stats.users_migrated,
                'analyses_migrated': streamlit_stats.analyses_migrated,
                'configs_migrated': streamlit_stats.configs_migrated,
                'errors': streamlit_stats.errors
            }
            
            # 2. 迁移分析结果数据
            self.logger.info("=== 第2步: 迁移分析结果数据 ===")
            results_migrator = AnalysisResultsMigrator()
            results_stats = await results_migrator.migrate_all_results()
            migration_results['results_migration'] = {
                'results_migrated': results_stats.results_migrated,
                'cache_entries_migrated': results_stats.cache_entries_migrated,
                'reports_migrated': results_stats.reports_migrated,
                'errors': results_stats.errors
            }
            
            # 3. 验证迁移结果
            self.logger.info("=== 第3步: 验证迁移结果 ===")
            streamlit_validation = await streamlit_migrator.validate_migration()
            results_validation = await results_migrator.validate_migration()
            
            migration_results['validation_results'] = {
                'streamlit_validation': streamlit_validation,
                'results_validation': results_validation
            }
            
            # 检查是否有严重错误
            total_errors = (
                len(streamlit_stats.errors) + 
                len(results_stats.errors) +
                len(streamlit_validation.get('validation_errors', [])) +
                len(results_validation.get('validation_errors', []))
            )
            
            migration_results['success'] = total_errors == 0
            migration_results['end_time'] = datetime.utcnow()
            
            # 记录迁移日志
            await self._write_migration_log(migration_results)
            
            self.logger.info(f"数据迁移完成，成功: {migration_results['success']}")
            
        except Exception as e:
            error_msg = f"数据迁移失败: {str(e)}"
            self.logger.error(error_msg)
            migration_results['errors'].append(error_msg)
            migration_results['success'] = False
            migration_results['end_time'] = datetime.utcnow()
        
        return migration_results
    
    async def run_partial_migration(self, migration_type: str) -> Dict[str, Any]:
        """运行部分迁移"""
        self.logger.info(f"开始部分迁移: {migration_type}")
        
        if migration_type == "streamlit":
            migrator = StreamlitDataMigrator()
            stats = await migrator.migrate_all_data()
            validation = await migrator.validate_migration()
            
            return {
                'type': 'streamlit',
                'stats': stats,
                'validation': validation,
                'success': len(stats.errors) == 0
            }
            
        elif migration_type == "results":
            migrator = AnalysisResultsMigrator()
            stats = await migrator.migrate_all_results()
            validation = await migrator.validate_migration()
            
            return {
                'type': 'results',
                'stats': stats,
                'validation': validation,
                'success': len(stats.errors) == 0
            }
            
        else:
            raise ValueError(f"不支持的迁移类型: {migration_type}")
    
    async def _write_migration_log(self, migration_results: Dict[str, Any]) -> None:
        """写入迁移日志"""
        try:
            log_content = []
            log_content.append(f"=== 数据迁移日志 ===")
            log_content.append(f"开始时间: {migration_results['start_time']}")
            log_content.append(f"结束时间: {migration_results['end_time']}")
            log_content.append(f"迁移成功: {migration_results['success']}")
            log_content.append("")
            
            # Streamlit迁移结果
            if migration_results['streamlit_migration']:
                sm = migration_results['streamlit_migration']
                log_content.append("=== Streamlit数据迁移 ===")
                log_content.append(f"用户迁移: {sm['users_migrated']}")
                log_content.append(f"分析记录迁移: {sm['analyses_migrated']}")
                log_content.append(f"配置迁移: {sm['configs_migrated']}")
                log_content.append(f"错误数量: {len(sm['errors'])}")
                if sm['errors']:
                    log_content.append("错误详情:")
                    for error in sm['errors']:
                        log_content.append(f"  - {error}")
                log_content.append("")
            
            # 分析结果迁移结果
            if migration_results['results_migration']:
                rm = migration_results['results_migration']
                log_content.append("=== 分析结果迁移 ===")
                log_content.append(f"结果文件迁移: {rm['results_migrated']}")
                log_content.append(f"缓存条目迁移: {rm['cache_entries_migrated']}")
                log_content.append(f"报告文件迁移: {rm['reports_migrated']}")
                log_content.append(f"错误数量: {len(rm['errors'])}")
                if rm['errors']:
                    log_content.append("错误详情:")
                    for error in rm['errors']:
                        log_content.append(f"  - {error}")
                log_content.append("")
            
            # 验证结果
            if migration_results['validation_results']:
                vr = migration_results['validation_results']
                log_content.append("=== 验证结果 ===")
                
                if 'streamlit_validation' in vr:
                    sv = vr['streamlit_validation']
                    log_content.append("Streamlit数据验证:")
                    log_content.append(f"  用户总数: {sv['users_count']}")
                    log_content.append(f"  分析记录总数: {sv['analyses_count']}")
                    log_content.append(f"  配置总数: {sv['configs_count']}")
                    if sv['validation_errors']:
                        log_content.append("  验证错误:")
                        for error in sv['validation_errors']:
                            log_content.append(f"    - {error}")
                
                if 'results_validation' in vr:
                    rv = vr['results_validation']
                    log_content.append("分析结果验证:")
                    log_content.append(f"  包含结果的分析: {rv['analyses_with_results']}")
                    log_content.append(f"  缓存条目: {rv['cache_entries']}")
                    log_content.append(f"  报告数量: {rv['reports_count']}")
                    if rv['validation_errors']:
                        log_content.append("  验证错误:")
                        for error in rv['validation_errors']:
                            log_content.append(f"    - {error}")
            
            # 写入日志文件
            with open(self.migration_log_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(log_content))
            
            self.logger.info(f"迁移日志已写入: {self.migration_log_file}")
            
        except Exception as e:
            self.logger.error(f"写入迁移日志失败: {e}")
    
    async def check_migration_prerequisites(self) -> Dict[str, bool]:
        """检查迁移前置条件"""
        self.logger.info("检查迁移前置条件...")
        
        prerequisites = {
            'database_connection': False,
            'redis_connection': False,
            'web_data_exists': False,
            'analysis_data_exists': False,
            'config_accessible': False
        }
        
        try:
            # 检查数据库连接
            try:
                from backend.core.database import get_database
                db = await get_database()
                await db.command('ping')
                prerequisites['database_connection'] = True
                self.logger.info("✓ 数据库连接正常")
            except Exception as e:
                self.logger.error(f"✗ 数据库连接失败: {e}")
            
            # 检查Redis连接
            try:
                from backend.core.redis_client import get_redis_client
                redis_client = await get_redis_client()
                await redis_client.ping()
                prerequisites['redis_connection'] = True
                self.logger.info("✓ Redis连接正常")
            except Exception as e:
                self.logger.error(f"✗ Redis连接失败: {e}")
            
            # 检查Web数据目录
            web_data_dir = project_root / "web" / "data"
            if web_data_dir.exists():
                prerequisites['web_data_exists'] = True
                self.logger.info(f"✓ Web数据目录存在: {web_data_dir}")
            else:
                self.logger.warning(f"✗ Web数据目录不存在: {web_data_dir}")
            
            # 检查分析数据目录
            analysis_data_dir = project_root / "data"
            if analysis_data_dir.exists():
                prerequisites['analysis_data_exists'] = True
                self.logger.info(f"✓ 分析数据目录存在: {analysis_data_dir}")
            else:
                self.logger.warning(f"✗ 分析数据目录不存在: {analysis_data_dir}")
            
            # 检查配置文件
            try:
                from tradingagents.default_config import DEFAULT_CONFIG
                prerequisites['config_accessible'] = True
                self.logger.info("✓ 配置文件可访问")
            except Exception as e:
                self.logger.error(f"✗ 配置文件访问失败: {e}")
            
        except Exception as e:
            self.logger.error(f"前置条件检查失败: {e}")
        
        return prerequisites


def setup_logging(log_level: str = "INFO"):
    """设置日志"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(project_root / "migration.log", encoding='utf-8')
        ]
    )


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="TradingAgents数据迁移工具")
    parser.add_argument(
        "--type", 
        choices=["full", "streamlit", "results", "check"], 
        default="full",
        help="迁移类型"
    )
    parser.add_argument(
        "--log-level", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
        default="INFO",
        help="日志级别"
    )
    parser.add_argument(
        "--skip-existing", 
        action="store_true",
        help="跳过已存在的数据"
    )
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    
    runner = MigrationRunner()
    
    if args.type == "check":
        # 检查前置条件
        prerequisites = await runner.check_migration_prerequisites()
        
        print("\n=== 迁移前置条件检查 ===")
        for condition, status in prerequisites.items():
            status_symbol = "✓" if status else "✗"
            print(f"{status_symbol} {condition}: {'通过' if status else '失败'}")
        
        all_passed = all(prerequisites.values())
        print(f"\n前置条件检查: {'全部通过' if all_passed else '存在问题'}")
        
        if not all_passed:
            print("请解决上述问题后再运行迁移")
            sys.exit(1)
    
    elif args.type == "full":
        # 完整迁移
        results = await runner.run_full_migration(args.skip_existing)
        
        print("\n=== 完整迁移结果 ===")
        print(f"迁移成功: {results['success']}")
        print(f"开始时间: {results['start_time']}")
        print(f"结束时间: {results['end_time']}")
        
        if results['streamlit_migration']:
            sm = results['streamlit_migration']
            print(f"\nStreamlit数据迁移:")
            print(f"  用户: {sm['users_migrated']}")
            print(f"  分析记录: {sm['analyses_migrated']}")
            print(f"  配置: {sm['configs_migrated']}")
            print(f"  错误: {len(sm['errors'])}")
        
        if results['results_migration']:
            rm = results['results_migration']
            print(f"\n分析结果迁移:")
            print(f"  结果文件: {rm['results_migrated']}")
            print(f"  缓存条目: {rm['cache_entries_migrated']}")
            print(f"  报告文件: {rm['reports_migrated']}")
            print(f"  错误: {len(rm['errors'])}")
        
        if not results['success']:
            print(f"\n迁移过程中发现错误，详细信息请查看日志文件")
            sys.exit(1)
    
    else:
        # 部分迁移
        results = await runner.run_partial_migration(args.type)
        
        print(f"\n=== {results['type']} 迁移结果 ===")
        print(f"迁移成功: {results['success']}")
        
        if hasattr(results['stats'], 'users_migrated'):
            print(f"用户迁移: {results['stats'].users_migrated}")
            print(f"分析记录迁移: {results['stats'].analyses_migrated}")
            print(f"配置迁移: {results['stats'].configs_migrated}")
        
        if hasattr(results['stats'], 'results_migrated'):
            print(f"结果文件迁移: {results['stats'].results_migrated}")
            print(f"缓存条目迁移: {results['stats'].cache_entries_migrated}")
            print(f"报告文件迁移: {results['stats'].reports_migrated}")
        
        print(f"错误数量: {len(results['stats'].errors)}")
        
        if not results['success']:
            sys.exit(1)
    
    print("\n迁移完成！")


if __name__ == "__main__":
    asyncio.run(main())