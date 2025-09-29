#!/usr/bin/env python3
"""
升级和回滚管理脚本
提供平滑的升级路径和回滚机制
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
import logging
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class UpgradeRollbackManager:
    """升级回滚管理器"""
    
    def __init__(self):
        self.project_root = project_root
        self.backup_dir = self.project_root / "upgrade_backups"
        self.logger = logging.getLogger(__name__)
        
        # 确保备份目录存在
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self) -> str:
        """创建系统备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        backup_path.mkdir(exist_ok=True)
        
        try:
            self.logger.info(f"创建系统备份到: {backup_path}")
            
            # 备份数据目录
            if (self.project_root / "web" / "data").exists():
                shutil.copytree(
                    self.project_root / "web" / "data",
                    backup_path / "web_data"
                )
                self.logger.info("✓ Web数据备份完成")
            
            if (self.project_root / "data").exists():
                shutil.copytree(
                    self.project_root / "data",
                    backup_path / "analysis_data"
                )
                self.logger.info("✓ 分析数据备份完成")
            
            # 备份配置文件
            config_backup = backup_path / "configs"
            config_backup.mkdir(exist_ok=True)
            
            config_files = [
                "tradingagents/default_config.py",
                ".env",
                "config.yaml",
                "config.json"
            ]
            
            for config_file in config_files:
                config_path = self.project_root / config_file
                if config_path.exists():
                    shutil.copy2(config_path, config_backup / config_path.name)
            
            self.logger.info("✓ 配置文件备份完成")
            
            # 创建备份信息文件
            backup_info = {
                "timestamp": timestamp,
                "backup_path": str(backup_path),
                "created_at": datetime.now().isoformat(),
                "system_info": {
                    "python_version": sys.version,
                    "platform": sys.platform
                }
            }
            
            with open(backup_path / "backup_info.json", 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            self.logger.info(f"✓ 系统备份创建完成: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"创建备份失败: {e}")
            return ""
    
    def perform_upgrade(self) -> bool:
        """执行系统升级"""
        try:
            self.logger.info("开始系统升级...")
            
            # 1. 创建备份
            backup_path = self.create_backup()
            if not backup_path:
                self.logger.error("备份创建失败，升级中止")
                return False
            
            # 2. 检查新系统依赖
            if not self._check_dependencies():
                self.logger.error("依赖检查失败，升级中止")
                return False
            
            # 3. 启动新系统服务
            if not self._start_new_services():
                self.logger.error("新系统启动失败，升级中止")
                return False
            
            # 4. 执行数据迁移
            if not self._run_data_migration():
                self.logger.error("数据迁移失败，开始回滚")
                self.rollback_from_backup(backup_path)
                return False
            
            # 5. 验证升级结果
            if not self._validate_upgrade():
                self.logger.error("升级验证失败，开始回滚")
                self.rollback_from_backup(backup_path)
                return False
            
            self.logger.info("✓ 系统升级完成")
            return True
            
        except Exception as e:
            self.logger.error(f"升级过程失败: {e}")
            return False
    
    def rollback_from_backup(self, backup_path: str) -> bool:
        """从备份回滚系统"""
        try:
            backup_path = Path(backup_path)
            if not backup_path.exists():
                self.logger.error(f"备份路径不存在: {backup_path}")
                return False
            
            self.logger.info(f"开始从备份回滚: {backup_path}")
            
            # 1. 停止新系统服务
            self._stop_new_services()
            
            # 2. 恢复数据目录
            if (backup_path / "web_data").exists():
                if (self.project_root / "web" / "data").exists():
                    shutil.rmtree(self.project_root / "web" / "data")
                shutil.copytree(
                    backup_path / "web_data",
                    self.project_root / "web" / "data"
                )
                self.logger.info("✓ Web数据恢复完成")
            
            if (backup_path / "analysis_data").exists():
                if (self.project_root / "data").exists():
                    shutil.rmtree(self.project_root / "data")
                shutil.copytree(
                    backup_path / "analysis_data",
                    self.project_root / "data"
                )
                self.logger.info("✓ 分析数据恢复完成")
            
            # 3. 恢复配置文件
            config_backup = backup_path / "configs"
            if config_backup.exists():
                for config_file in config_backup.iterdir():
                    target_path = self.project_root / config_file.name
                    shutil.copy2(config_file, target_path)
                self.logger.info("✓ 配置文件恢复完成")
            
            # 4. 启动旧系统
            self._start_old_services()
            
            self.logger.info("✓ 系统回滚完成")
            return True
            
        except Exception as e:
            self.logger.error(f"回滚失败: {e}")
            return False
    
    def _check_dependencies(self) -> bool:
        """检查新系统依赖"""
        try:
            # 检查Python依赖
            required_packages = [
                "fastapi", "uvicorn", "motor", "redis", "pydantic"
            ]
            
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    self.logger.error(f"缺少依赖包: {package}")
                    return False
            
            # 检查Node.js依赖（如果需要）
            frontend_dir = self.project_root / "frontend"
            if frontend_dir.exists():
                node_modules = frontend_dir / "node_modules"
                if not node_modules.exists():
                    self.logger.warning("前端依赖未安装，尝试安装...")
                    result = subprocess.run(
                        ["npm", "install"],
                        cwd=frontend_dir,
                        capture_output=True,
                        text=True
                    )
                    if result.returncode != 0:
                        self.logger.error("前端依赖安装失败")
                        return False
            
            self.logger.info("✓ 依赖检查通过")
            return True
            
        except Exception as e:
            self.logger.error(f"依赖检查失败: {e}")
            return False
    
    def _start_new_services(self) -> bool:
        """启动新系统服务"""
        try:
            # 启动后端服务
            backend_cmd = [
                sys.executable, "-m", "uvicorn", "main:app",
                "--host", "0.0.0.0", "--port", "8000", "--reload"
            ]
            
            backend_process = subprocess.Popen(
                backend_cmd,
                cwd=self.project_root / "backend",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 等待服务启动
            import time
            time.sleep(5)
            
            # 检查服务是否正常运行
            if backend_process.poll() is not None:
                self.logger.error("后端服务启动失败")
                return False
            
            # 启动前端服务（如果存在）
            frontend_dir = self.project_root / "frontend"
            if frontend_dir.exists():
                frontend_cmd = ["npm", "start"]
                frontend_process = subprocess.Popen(
                    frontend_cmd,
                    cwd=frontend_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                time.sleep(5)
                if frontend_process.poll() is not None:
                    self.logger.warning("前端服务启动失败，但继续升级")
            
            self.logger.info("✓ 新系统服务启动完成")
            return True
            
        except Exception as e:
            self.logger.error(f"启动新系统服务失败: {e}")
            return False
    
    def _stop_new_services(self) -> bool:
        """停止新系统服务"""
        try:
            # 停止后端服务
            subprocess.run(["pkill", "-f", "uvicorn main:app"], check=False)
            
            # 停止前端服务
            subprocess.run(["pkill", "-f", "npm start"], check=False)
            
            self.logger.info("✓ 新系统服务已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止新系统服务失败: {e}")
            return False
    
    def _start_old_services(self) -> bool:
        """启动旧系统服务"""
        try:
            # 启动Streamlit应用
            old_app_cmd = [sys.executable, "run_web.py"]
            
            subprocess.Popen(
                old_app_cmd,
                cwd=self.project_root / "web",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.logger.info("✓ 旧系统服务已启动")
            return True
            
        except Exception as e:
            self.logger.error(f"启动旧系统服务失败: {e}")
            return False
    
    def _run_data_migration(self) -> bool:
        """运行数据迁移"""
        try:
            migration_cmd = [
                sys.executable, "backend/scripts/migration/run_migration.py",
                "--type", "full"
            ]
            
            result = subprocess.run(
                migration_cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"数据迁移失败: {result.stderr}")
                return False
            
            self.logger.info("✓ 数据迁移完成")
            return True
            
        except Exception as e:
            self.logger.error(f"数据迁移失败: {e}")
            return False
    
    def _validate_upgrade(self) -> bool:
        """验证升级结果"""
        try:
            # 运行验证脚本
            validation_cmd = [
                sys.executable, "backend/scripts/migration/validate_migration.py"
            ]
            
            result = subprocess.run(
                validation_cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"升级验证失败: {result.stderr}")
                return False
            
            # 测试API兼容性
            try:
                import requests
                response = requests.get("http://localhost:8000/api/legacy/health", timeout=10)
                if response.status_code != 200:
                    self.logger.error("API兼容性测试失败")
                    return False
            except Exception as e:
                self.logger.error(f"API测试失败: {e}")
                return False
            
            self.logger.info("✓ 升级验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"升级验证失败: {e}")
            return False
    
    def list_backups(self) -> list:
        """列出可用的备份"""
        backups = []
        
        try:
            for backup_dir in self.backup_dir.iterdir():
                if backup_dir.is_dir() and backup_dir.name.startswith("backup_"):
                    info_file = backup_dir / "backup_info.json"
                    if info_file.exists():
                        with open(info_file, 'r') as f:
                            backup_info = json.load(f)
                        backups.append(backup_info)
            
            # 按时间排序
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"列出备份失败: {e}")
        
        return backups


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="TradingAgents升级回滚管理工具")
    parser.add_argument(
        "action",
        choices=["upgrade", "rollback", "backup", "list-backups"],
        help="执行的操作"
    )
    parser.add_argument(
        "--backup-path",
        help="回滚时使用的备份路径"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别"
    )
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    manager = UpgradeRollbackManager()
    
    if args.action == "backup":
        backup_path = manager.create_backup()
        if backup_path:
            print(f"✓ 备份创建成功: {backup_path}")
        else:
            print("✗ 备份创建失败")
            sys.exit(1)
    
    elif args.action == "upgrade":
        success = manager.perform_upgrade()
        if success:
            print("✓ 系统升级成功")
        else:
            print("✗ 系统升级失败")
            sys.exit(1)
    
    elif args.action == "rollback":
        if not args.backup_path:
            # 使用最新的备份
            backups = manager.list_backups()
            if not backups:
                print("✗ 没有可用的备份")
                sys.exit(1)
            backup_path = backups[0]['backup_path']
        else:
            backup_path = args.backup_path
        
        success = manager.rollback_from_backup(backup_path)
        if success:
            print(f"✓ 系统回滚成功: {backup_path}")
        else:
            print("✗ 系统回滚失败")
            sys.exit(1)
    
    elif args.action == "list-backups":
        backups = manager.list_backups()
        if backups:
            print("可用的备份:")
            for backup in backups:
                print(f"  - {backup['timestamp']}: {backup['backup_path']}")
                print(f"    创建时间: {backup['created_at']}")
        else:
            print("没有可用的备份")


if __name__ == "__main__":
    main()