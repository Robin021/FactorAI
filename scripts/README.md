# Scripts 目录说明

## 📁 目录结构

```
scripts/
├── archive/          # 归档的历史脚本
├── backup/           # 数据库备份脚本
├── docker/           # Docker相关脚本
├── release/          # 发布工具
├── setup/            # 初始化脚本
├── validation/       # 系统验证脚本
└── [根目录脚本]      # 常用快捷脚本
```

## 🚀 常用脚本

### 启动和管理

```bash
# Docker智能启动
./scripts/smart_start.sh          # Linux/Mac
powershell scripts/smart_start.ps1  # Windows

# 用户管理
python scripts/user_password_manager.py list
python scripts/user_password_manager.py change-password admin
```

### 初始化

```bash
# 数据库初始化
python scripts/setup/init_database.py

# 系统状态检查
python scripts/validation/check_system_status.py
```

### 备份和恢复

```bash
# MongoDB备份
./scripts/backup/backup-mongodb.sh

# Redis备份
./scripts/backup/backup-redis.sh
```

## 📋 脚本分类

### setup/ - 初始化脚本
- `init_database.py` - 数据库初始化
- `setup_databases.py` - 数据库配置

### docker/ - Docker脚本
- `mongo-init.js` - MongoDB初始化脚本
- `health-check.sh` - 容器健康检查

### backup/ - 备份脚本
- `backup-mongodb.sh` - MongoDB备份
- `backup-redis.sh` - Redis备份
- `restore-mongodb.sh` - MongoDB恢复
- `restore-redis.sh` - Redis恢复

### validation/ - 验证脚本
- `check_system_status.py` - 系统状态检查
- `check_dependencies.py` - 依赖检查

### release/ - 发布工具
- `prepare_release.py` - 发布准备
- `cleanup_directories.py` - 目录清理
- `verify_cleanup.sh` - 清理验证

### archive/ - 历史归档
包含历史开发过程中的临时脚本和工具

## 🔗 相关文档

- [用户管理指南](../docs/guides/user-management.md)
- [Docker部署指南](../docs/deployment/docker-guide.md)
- [系统维护指南](../docs/maintenance/system-maintenance.md)

---

**最后更新**: 2025-10-24
**版本**: cn-v1.0
